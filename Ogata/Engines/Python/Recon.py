from ...Globals import *;
from ... import Type;





rVAR: re.Pattern[str] = re.compile(r"([A-Za-z_\.]+(?=: [\S ]+ = ))|([[A-Za-z_\.]+(?= = ))|([A-Za-z_\.]+(?=: [\w\.\[\]\"\']+;$))|(?:(?<=def) \w+\()(.+(?=\):|\) ))");
rVAR_Type: re.Pattern[str] = re.compile(r"(?!:)(?:[A-Za-z_\.]*: )[a-zA-Z_,\.\[\] \|]*(?==|;?$)");
rVAR_For: re.Pattern[str] = re.compile(r"(?<=for )[a-zA-Z_, ]+(?= in)");
rVAR_Func: re.Pattern[str] = re.compile(r"(?<=[ \t])#[ \w\.\'\"\[\]\#\:]+(?=$)");

rComment: re.Pattern[str] = re.compile(r"(?<=[ \t])#[ \w\.\'\"\[\]\#\:\*]+(?=$)");

rFUNCTION: re.Pattern[str] = re.compile(r"(?<=def )[A-Za-z_]+(?=\()");

rWHITESPACE: re.Pattern[str] = re.compile(r"^[\t ]+(?=\w)");

rIMPORT_Bool: re.Pattern[str] = re.compile(r"from.+|import.+");





def _Digest_File(String: str) -> list[str]:
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
				Data[ln] = f"";
		if (inDSTR): Data[ln] = "";

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



			lnG: int = -1;
			for m in rVAR.finditer(l): # pyright: ignore[reportUnusedVariable]
				for gn, g in enumerate(m.groups()):
					# Validity Checks
					if (not g or g == ""): continue;
					if (g.startswith("Config.")): continue; # Ignore TSNA Config.*

					Log.Debug(f"lnG: {lnG} - gn: {gn} - g: {g}");
					if (gn in [0, 2, 3]):
						Log.Debug(f"{l.strip()} (line {ln}) | gn: {gn} | g: {g}");
						ms = rVAR_Type.findall(g if (gn == 3) else l);
						if (g in ["else", "elif"]): continue; # Banned "detected variable names"
						typeData: str = ms[0].split(":");
						if (len(typeData) < 2): continue; # I am horrible at regex
						typeData = typeData[1].strip();

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

						Variables[g]["Type"].add(typeData);
					else:
						if (lnG == 0): lnG = 1; continue;
						lnG = 1;

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

				Log.Debug(f"{ln} {m.start()}:{m.end()} @ {m.group()}");

		return Variables;



	@staticmethod
	def Semicolon(P: str) -> list[Type.Recon_Base]:
		Data: list[str] = _Digest_File(cast(str, File.Read(P)));

		Semicolons: list[Type.Recon_Base] = [];
		for ln, l in enumerate(Data):
			for m in rComment.finditer(l):
				l = l[:m.start()];
			Data[ln] = l.strip();

		Complex: int = 0;
		for ln, l in enumerate(Data, start=1):
			if (l == ""): continue;

			if (l.startswith("@")): Log.Debug(f"Ignored: {l}"); continue;
			if (l.endswith(":")): Log.Debug(f"Ignored: {l}"); continue;

			if (any(l.endswith(x) for x in ["[", "{", "(", ","])): Complex += 1; Log.Debug(f"Complex: Ignored {l}"); continue;
			if (any(x in l for x in ["]", "}", ")"])): Complex -= 1; Log.Debug(f"Complex: {l}");
			if (Complex < 0): Complex = 0;
			if (Complex > 0): continue;


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
		Data: list[str] = _Digest_File(cast(str, File.Read(P)));

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