from ...Globals import *;
from ... import Type;





rVAR: re.Pattern[str] = re.compile(r"([A-Za-z_\.]+(?=: [\S ]+ = ))|([[A-Za-z_\.]+(?= = ))|([A-Za-z_\.]+(?=: [\w\.\[\]\"\']+;$))|(?:(?<=def) \w+\()(.+(?=\):|\) ))");
rVAR_Type: re.Pattern[str] = re.compile(r"(?!:)(?:[A-Za-z_\.]*: )[a-zA-Z_,\.\[\] \|/]*(?==|;?$)");
rVAR_For: re.Pattern[str] = re.compile(r"(?<=for )[a-zA-Z_, ]+(?= in)");
rVAR_Func: re.Pattern[str] = re.compile(r"^def [^\(]+\((.+)\)");
rVAR_FuncArg: re.Pattern[str] = re.compile(r"(\w+)((?:: ).+)?");

rCOMMENT: re.Pattern[str] = re.compile(r"(?:(?<=[ \t])#|^#).+(?=$)", flags=re.MULTILINE);
rSTRING: re.Pattern[str] = re.compile(r"(?<=([\"\']))(?:(?=(\\?))\2.)*?(?=\1)");

rFUNCTION: re.Pattern[str] = re.compile(r"(?<=def )[A-Za-z_]+(?=\()");

rWHITESPACE: re.Pattern[str] = re.compile(r"^[\t ]+(?=\w)");

rIMPORT_Bool: re.Pattern[str] = re.compile(r"from.+|import.+");





def _Digest_File(String: str, noComments: bool = True) -> list[str]:
	""" Returns a digestible file for Recon """
	Data: list[str] = [x.replace("¤N¤", "\\n") for x in String.replace("\\n", "¤N¤").split("\n")];

	# Clear DocStrings
	inDSTR: bool = False;
	for ln, l in enumerate(Data):
		quotes: list[str] = l.split(f"\"\"\"");
		if (len(quotes) == 1 and not inDSTR): continue;
		else:
			# You could use math here to calculate the final state of inDSTR but I'm lazy
			for i in range (len(quotes) - 1): # pyright: ignore[reportUnusedVariable]
				inDSTR = False if (inDSTR) else True;
				Data[ln] = "" if (noComments) else "#";
		if (inDSTR): Data[ln] = "" if (noComments) else "#";

	return Data;



class Get:
	@staticmethod
	def Variables(P: str) -> dict[str, Type.Recon_Variable]:
		Data: list[str] = _Digest_File(cast(str, File.Read(P)));

		Variables: dict[str, Type.Recon_Variable] = {};
		Functions: list[str] = ["--ROOT--"];
		White_Last: int = 0;

		for ln, l in enumerate(Data, start=1):
			# Function Context Detection
			findfunc: list[str] = rFUNCTION.findall(l);
			white_next: list[str] = rWHITESPACE.findall(Data[min(ln, len(Data) - 1)]); # Remeber ln starts at 1 not 0
			white_curr: list[str] = rWHITESPACE.findall(Data[ln - 1]);

			if (len(findfunc) > 0):
				Functions.append(findfunc[0]);
				if (len(white_next) > 0):
					White_Last = len(white_next[0]);
			else:
				if (len(white_curr) > 0):
					if (len(white_curr[0]) < White_Last):
						White_Last = len(white_curr[0]);
						Functions.pop();



			"""
			TBD, currently breaks too much
			# Function Argument Detection
			for m in rVAR_Func.finditer(l):
				if (not m.group(1)): continue;
				for arg in m.group(1).split(","):
					for m_sub in rVAR_FuncArg.finditer(arg):
						an: str = m_sub.group(1).strip();
						if (an not in Variables.keys()): Variables[an] = {
							"Path": [], "Line": [], "String": [],
							"Count": {}, "Type": set(),
							"Constant": an.isupper(), "Temporary": an.islower()
						};
						Variables[an]["Path"].append(P);
						Variables[an]["Line"].append(ln);
						Variables[an]["String"].append(l);
						if (Functions[-1] not in Variables[an]["Count"].keys()): Variables[an]["Count"][Functions[-1]] = 0;
						Variables[an]["Count"][Functions[-1]] += 1;

						if (m_sub.group(2)):
							Variables[an]["Type"].add(m_sub.group(2)[1:].strip());
							# [1:] to remove the `:`, strip to remove the possible ` ` after the `:`
			"""


			# General Variable Detection
			lnG: int = -1;
			for m in rVAR.finditer(l):
				for gn, g in enumerate(m.groups()):
					# Validity Checks
					if (not g or g == ""): continue;
					if (g.startswith("Config.")): continue; # Ignore TSNA Config.*

					Log.Debug(f"lnG: {lnG} - gn: {gn} - g: {g}");
					if (gn in [0, 2, 3]):
						if (g in ["else", "elif", "self"]): continue; # Banned "detected variable names"
						Log.Debug(f"{l.strip()} | gn: {gn} | g: {g}\n {P}, line {ln}");

						tdata: list[str] | None = None;
						for ms in rVAR_Type.finditer(g if (gn == 3) else l):
							tdata = ms[0].split(":");
						# I don't know why, I don't wanna know why
						# but re.findall is so fucking garbage we have to do this abomination

						if (not tdata): continue;
						if (len(tdata) < 2): continue; # I am horrible at regex
						tData: str = tdata[1].strip();

						lnG = 0;

						if (g not in Variables.keys()): Variables[g] = {
							"Path": [], "Line": [], "String": [],
							"Count": {}, "Type": set(),
							"Constant": g.isupper(), "Temporary": g.islower()
						};
						Variables[g]["Path"].append(P);
						Variables[g]["Line"].append(ln);
						Variables[g]["String"].append(l);
						if (Functions[-1] not in Variables[g]["Count"].keys()): Variables[g]["Count"][Functions[-1]] = 0;
						Variables[g]["Count"][Functions[-1]] += 1;

						Variables[g]["Type"].add(tData);
					else:
						if (lnG == 0): lnG = 1; continue;
						lnG = 1;

						# Variable Unpacking is not handled correctly unless we do THIS abomination! Python doesn't support typed variable unpacking so it's a pretty safe bet to run this only here
						vars: list[str] = [];
						buffer: str = ""; complex: int = 0;
						for i, m in enumerate(rSTRING.finditer(l)): # Copy pasted courtesy of Semicolon, will need to be optimized later
							if (i%2 != 0): continue; # Ignore when pair number because otherwise replaces things in between two quoted stuff which breaks everything
							for c in l[:m.start()] + ("¤" * (m.end() - m.start())) + l[m.end():]:
								if (c in ["[", "(", "{"]): complex += 1;
								elif (c in ["]", ")", "}"]): complex -= 1;
								if (c == "," and complex == 0): vars.append(buffer.strip()); buffer = "";
								if (c == "="): vars.append(buffer.strip()); break;
								buffer += c;
						del buffer; del complex;

						for v in vars:
							if (v not in Variables.keys()): Variables[v] = {
								"Path": [], "Line": [], "String": [],
								"Count": {}, "Type": set(),
								"Constant": v.isupper(), "Temporary": v.islower()
							};

							Variables[v]["Path"].append(P);
							Variables[v]["Line"].append(ln);
							Variables[v]["String"].append(l);
							if (Functions[-1] not in Variables[v]["Count"].keys()): Variables[v]["Count"][Functions[-1]] = 0;
							Variables[v]["Count"][Functions[-1]] += 1;
						del vars;

				Log.Debug(f"{ln} {m.start()}:{m.end()} @ {m.group()}");

		return Variables;



	@staticmethod
	def Semicolon(P: str) -> list[Type.Recon_Base]:
		Data: list[str] = _Digest_File(cast(str, File.Read(P)));
		Data_LT: list[str] = [];


		# I shouldn't be allowed to write Python anymore. God is dead and we're all in hell being tormented
		Semicolons: list[Type.Recon_Base] = [];
		for ln, l in enumerate(Data): # Strip out comments
			lt: str = l;
			for i, m in enumerate(rSTRING.finditer(l)):
				if (i%2 != 0): continue; # Ignore when pair number because otherwise replaces things in between two quoted stuff which breaks everything
				Log.Debug(f"GROUPS: {m.groups()} | START: {m.start()} - END: {m.end()} | IN QUOTES: {m.group()}\nLINE: {l}\nFINE: {lt[:m.start()] + ("¤" * (m.end() - m.start())) + lt[m.end():]}");
				lt = lt[:m.start()] + ("¤" * (m.end() - m.start())) + lt[m.end():];

			for m in rCOMMENT.finditer(lt):
				Log.Debug(f"GROUP: {m.group()} | START: {m.start()} - END: {m.end()}\nLT:\t{lt}\nL :\t{l}\nF :{l[:m.start()]}");
				l = l[:m.start()];

			Data[ln] = l.strip();
			Data_LT.append(lt);

		#File.Write(f"DEBUG_{Time.Get_Unix(True)}.txt", f"\n".join(Data));
		#File.Write(f"DEBUG-LT_{Time.Get_Unix(True)}.txt", f"\n".join(Data_LT));
		del lt; # pyright: ignore[reportPossiblyUnboundVariable]



		Complex: int = 0;
		for ln, l in enumerate(Data, start=1):
			if (l == ""): continue;
			if (l.startswith("@")): Log.Debug(f"Ignored: {l}"); continue;
			if (l.endswith(":")): Log.Debug(f"Ignored: {l}"); continue;


			pcomplex: int = Complex;
			for c in Data_LT[ln - 1]:
				if (c in ["[", "(", "{"]): Complex += 1;
				elif (c in ["]", ")", "}"]): Complex -= 1;

			if (pcomplex != Complex): Log.Debug(f"Post Complex: {pcomplex} → {Complex} ({pcomplex - Complex})\nFile {P}, line {ln}\n\t{l}");
			del pcomplex;


			if (Complex > 0): Log.Debug(f"Complex [{Complex}] Ignored: {l}"); continue;
			if (not l.endswith(";")):
				Semicolons.append(cast(Type.Recon_Base, {
					"Path": [P],
					"Line": [ln],
					"String": [l]
				}));

		return Semicolons;



	@staticmethod
	def Fors(P: str) -> list[Type.Recon_For]:
		Data: list[str] = _Digest_File(cast(str, File.Read(P)));

		Fors: list[Type.Recon_For] = [];
		for ln, l in enumerate(Data, start=1):
			for m in rVAR_For.finditer(l):
				string: str = l[m.start():m.end()];
				if (not string.islower()):
					for var in string.split(", "):
						Fors.append(cast(Type.Recon_For, {
							"Path": [P],
							"Line": [ln],
							"String": [l],
							"Variable": var
						}));
		return Fors;



	@staticmethod
	def Whitespaces(P: str) -> list[Type.Recon_Base]:
		Data: list[str] = _Digest_File(cast(str, File.Read(P)));

		Whitespaces: list[Type.Recon_Base] = [];
		for ln, l in enumerate(Data, start=1):
			for m in rWHITESPACE.finditer(l):
				string: str = l[m.start():m.end()];
				if (" " not in string): continue;

				Whitespaces.append(cast(Type.Recon_Base, {
					"Path": [P],
					"Line": [ln],
					"String": [string]
				}));

		return Whitespaces;



	@staticmethod
	def Spacings(P: str) -> list[Type.Recon_Base]:
		Data: list[str] = _Digest_File(cast(str, File.Read(P)), False);

		Spacings: list[Type.Recon_Base] = [];

		cspacing: int = 0;
		last: int = -1;
		for ln, l in enumerate(Data, start=1):
			if (l == ""): cspacing += 1; continue;
			if (rIMPORT_Bool.match(l)):
				last = 0;
				if (cspacing not in [0, 3, 5, 8, 10] and (cspacing > 2)):
					Spacings.append({
						"Path": [P],
						"Line": [ln],
						"String": [str(cspacing)]
					});
				cspacing = 0;
			if (len(rFUNCTION.findall(l)) > 0):
				last = 1;
				if (cspacing not in [0, 3, 5, 8, 10]):
					Spacings.append({
						"Path": [P],
						"Line": [ln],
						"String": [str(cspacing)]
					});

			# Decorator Case
			if (l.strip().startswith("@")): continue;
			if (last == 0):
				if (cspacing not in [0, 3, 5, 8, 10] and (cspacing > 2)):
					Spacings.append({
						"Path": [P],
						"Line": [ln],
						"String": [str(cspacing)]
					});
			cspacing = 0;


		return Spacings;






__all__: list[str] = [
	"Get"
];