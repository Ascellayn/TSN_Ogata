from Ogata import *;





Variables: dict[str, Type.Recon_Variable] = {};
Semicolons: list[Type.Recon_Base] = [];
Fors: list[Type.Recon_For] = [];
Whitespaces: list[Type.Recon_Base] = [];
Spacings: list[Type.Recon_Base] = [];

Errors: list[str] = [];
Warnings: list[str] = [];





def Culprit(RC: Type.Recon_Base) -> str:
	Text: str = "";
	for i in range (len(RC["Path"])):
		Text += f"File {RC['Path'][i]}, line {RC['Line'][i]}\n\t\"{RC['String'][i].strip()}\"\n";

	return Text;





def Execute() -> bool:
	# Config Checks
	Log.Stateless("Reading Otaga Config...");
	try: C: Type.Otaga_Config = cast(Type.Otaga_Config, File.JSON_Read("Config.json"));
	except Exception as E: Log.Awaited().EXCEPTION(E); exit(1);

		# Validation
	if (C == {}): Log.Critical(f"Otaga wasn't configured! Quitting."); exit(1);
	if ("Watch" not in C.keys()): Log.Critical(f"Missing \"Watch\" key! Quitting."); exit(1);
	if (type(C["Watch"]) != list): Log.Critical(f"\"Watch\" key contains an invalid data type! Quitting."); exit(1);

	Log.Awaited().OK();
	return Verify(C);





def Verify(Otaga: Type.Otaga_Config) -> bool:
	def Recon_Recursive(P: str) -> None:
		l: File.Folder_Contents = File.List(P);
		for f in l[1]:
			if (f.endswith(".py")):
				Recon_Concat(Python.Recon.Get.Variables(f"{P}/{f}"));
				Recon_Concat_Semicolon(Python.Recon.Get.Semicolon(f"{P}/{f}"));
				Recon_Concat_Fors(Python.Recon.Get.Fors(f"{P}/{f}"));
				Recon_Concat_Whitespaces(Python.Recon.Get.Whitespaces(f"{P}/{f}"));
				Recon_Concat_Spacings(Python.Recon.Get.Spacings(f"{P}/{f}"));

		for f in l[0]: Recon_Recursive(f"{P}/{f}");



	def Recon_Concat(V: dict[str, Type.Recon_Variable]) -> None:
		global Variables;
		for key in V.keys():
			if (not key in Variables.keys()): Variables[key] = V[key];
			else:
				for func in V[key]["Count"].keys():
					if (func in Variables[key]["Count"]): Variables[key]["Count"][func] += V[key]["Count"][func];
					else: Variables[key]["Count"][func] = V[key]["Count"][func];
				for t in V[key]["Type"]: Variables[key]["Type"].add(t);



	def Recon_Concat_Semicolon(S: list[Type.Recon_Base]) -> None:
		global Semicolons;
		Semicolons += S;



	def Recon_Concat_Fors(S: list[Type.Recon_For]) -> None:
		global Fors;
		Fors += S;



	def Recon_Concat_Whitespaces(S: list[Type.Recon_Base]) -> None:
		global Whitespaces;
		Whitespaces += S;



	def Recon_Concat_Spacings(S: list[Type.Recon_Base]) -> None:
		global Spacings;
		Spacings += S;





	for watched in Otaga["Watch"]:
		Recon_Recursive(f"{watched}");
	
	for var in Variables.items():
		if (var[1]["Temporary"]): continue;
		if (len(var[1]["Type"]) == 0): Errors.append(f"{var[0]}: Undefined Type! \n{Culprit(var[1])}");
		if (len(var[1]["Type"]) > 1): Errors.append(f"{var[0]}: Type redefined {len(var[1]['Type'])} times! ({', '.join(var[1]['Type'])})\n{Culprit(var[1])}");
		for func in var[1]["Count"].keys():
			if (var[1]["Constant"] and var[1]["Count"][func] > 1): Errors.append(f"{var[0]}: Constant redefined {var[1]["Count"]} times!\n{Culprit(var[1])}");

		for t in var[1]["Type"]:
			if ("Any" in t):
				Warnings.append(f"{var[0]}: Type \"{t}\" contains \"Any\" which is discouraged.\n{Culprit(var[1])}");
	
	for semicolon in Semicolons:
		Errors.append(f"Missing Semicolon!\n{Culprit(semicolon)}");
	for badfor in Fors:
		Errors.append(f"Variable \"{badfor["Variable"]}\" used in For Loop isn't Lowercase!\n{Culprit(badfor)}");
	for whitespace in Whitespaces:
		Errors.append(f"Spaces are used instead of tabs!\nFile {whitespace['Path'][0]}, line {whitespace['Line'][0]}");
	for spacing in Spacings:
		Errors.append(f"Bad spacing: Must be 0, 3, 5, 8 or 10 linebreaks long, got {spacing['String'][0]}.\nFile {spacing['Path'][0]}, line {spacing['Line'][0]}");

	for warning in Warnings: Log.Warning(warning);
	for error in Errors: Log.Error(error);

	if (len(Errors) > 0):
		Log.Critical(f"Otaga finished: {len(Errors)} Errors - {len(Warnings)} Warnings");
		exit(1);

	if (len(Warnings) > 0):
		Log.Error(f"Otaga finished: {len(Warnings)} Warnings");
		exit(0);

	Log.Info(f"Otaga finished: No errors!");
	return True;





if (__name__ == "__main__"):
	TSN_Abstracter.App_Init(True);
	Execute();