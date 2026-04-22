from ...Globals import *;
from ... import Type;





rVAR: re.Pattern[str] = re.compile(r"([A-Za-z_\.]*(?=: [\S ]+ = ))|([[A-Za-z_\.]*(?= = ))", flags=re.MULTILINE | re.UNICODE);
rVAR_Type: re.Pattern[str] = re.compile(r"(?!:)(?:[A-Za-z_\.]*: )[a-zA-Z_,\.\[\] \|]*(?==)", flags=re.MULTILINE | re.UNICODE);
rVAR_For: re.Pattern[str] = re.compile(r"(?<=for )[a-zA-Z_, ]+(?= in)", flags=re.MULTILINE | re.UNICODE);

rComment: re.Pattern[str] = re.compile(r"(?<=[ \t])#[ \S]+(?=$)", flags=re.MULTILINE | re.UNICODE);

rFUNCTION: re.Pattern[str] = re.compile(r"(?<=def )[A-Za-z_]+(?=\()", flags=re.MULTILINE | re.UNICODE);

rWHTIESPACE: re.Pattern[str] = re.compile(r"^[\t ]+(?=\w)", flags=re.MULTILINE | re.UNICODE);

rIMPORT_Bool: re.Pattern[str] = re.compile(r"from.+|import.+", flags=re.MULTILINE | re.UNICODE);





class Get:
	@staticmethod
	def Variables(P: str) -> dict[str, Type.Recon_Variable]:
		D: str = cast(str, File.Read(P));
		Data: list[str] = [x.replace("¤N¤", "\\n") for x in D.replace("\\n", "¤N¤").split("\n")];

		Variables: dict[str, Type.Recon_Variable] = {};
		Function: str = "--ROOT--";
		for ln, l in enumerate(Data, start=1):
			findfunc: list[str] = rFUNCTION.findall(l);
			if (len(findfunc) > 0): Function = findfunc[0];

			lnG: int = -1;
			for m in rVAR.finditer(l): # pyright: ignore[reportUnusedVariable]
				for gn, g in enumerate(m.groups()):
					# Validity Checks
					if (not g or g == ""): continue;
					if (g.startswith("Config.")): continue; # Ignore TSNA Config.*

					Log.Debug(f"lnG: {lnG} - gn: {gn} - g: {g}");
					if (gn == 0):
						ms = rVAR_Type.findall(l);
						if (not ms): continue; # This check is here because cosmic rays. I honestly don't know the regex101 is entirely fine but in practice it's not.
						typeData: str = ms[0].split(":")[1].strip();

						lnG = 0;

						if (g not in Variables.keys()): Variables[g] = {
							"Path": [], "Line": [], "String": [],
							"Count": {}, "Type": set(),
							"Constant": g.isupper(), "Temporary": g.islower()
						};
						Variables[g]["Path"].append(P);
						Variables[g]["Line"].append(ln);
						Variables[g]["String"].append(l);
						if (Function not in Variables[g]["Count"].keys()): Variables[g]["Count"][Function] = 0;
						Variables[g]["Count"][Function] += 1;

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
						if (Function not in Variables[g]["Count"].keys()): Variables[g]["Count"][Function] = 0;
						Variables[g]["Count"][Function] += 1;

				Log.Debug(f"{ln} {m.start()}:{m.end()} @ {m.group()}");

		return Variables;



	@staticmethod
	def Semicolon(P: str) -> list[Type.Recon_Base]:
		D: str = cast(str, File.Read(P));
		Data: list[str] = [x.replace("¤N¤", "\\n") for x in D.replace("\\n", "¤N¤").split("\n")];

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
		D: str = cast(str, File.Read(P));
		Data: list[str] = [x.replace("¤N¤", "\\n") for x in D.replace("\\n", "¤N¤").split("\n")];

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
		D: str = cast(str, File.Read(P));
		Data: list[str] = [x.replace("¤N¤", "\\n") for x in D.replace("\\n", "¤N¤").split("\n")];

		Whitespaces: list[Type.Recon_Base] = [];
		for ln, l in enumerate(Data, start=1):
			for m in rWHTIESPACE.finditer(l):
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
		D: str = cast(str, File.Read(P));
		Data: list[str] = [x.replace("¤N¤", "\\n") for x in D.replace("\\n", "¤N¤").split("\n")];

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