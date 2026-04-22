from Ogata import *;





Variables: dict[str, Type.Recon_Variable] = {};
Semicolons: list[Type.Recon_Base] = [];
Fors: list[Type.Recon_For] = [];
Whitespaces: list[Type.Recon_Base] = [];
Spacings: list[Type.Recon_Base] = [];

Processed: int = 0;
Processed_Unix: float;
Errors: list[str] = [];
Warnings: list[str] = [];





def Culprit(RC: Type.Recon_Base) -> str:
	Text: str = "";
	for i in range (len(RC["Path"])):
		Text += f"File {RC['Path'][i]}, line {RC['Line'][i]}\n\t\"{RC['String'][i].strip()}\"\n";

	return Text;





def Execute() -> bool:
	# Config Checks
	if (not File.Exists("Ogata.json")):
		if (not File.Exists("../Ogata.json")):
			Log.Critical(f"Ogata Configuration file is missing!");
			exit(2);
		else: cpath: str = "../Ogata.json";
	else: cpath: str = "Ogata.json";

	Log.Stateless("Reading Ogata Config...");
	try: C: Type.Ogata_Config = cast(Type.Ogata_Config, File.JSON_Read(cpath));
	except Exception as E: Log.Awaited().EXCEPTION(E); exit(1);
	del cpath;

		# Validation
	if (C == {}): Log.Critical(f"Ogata wasn't configured! Quitting."); exit(1);
	if ("Watch" not in C.keys()): Log.Critical(f"Missing \"Watch\" key! Quitting."); exit(1);
	if (type(C["Watch"]) != list): Log.Critical(f"\"Watch\" key contains an invalid data type! Quitting."); exit(1);

	Log.Awaited().OK();
	return Verify(C);





def Verify(Ogata: Type.Ogata_Config) -> bool:
	global Processed_Unix; Processed_Unix = Time.Get_Unix(True);
	def Recon_Recursive(P: str) -> None:
		global Processed, Semicolons, Fors, Whitespaces, Spacings;
		l: File.Folder_Contents = File.List(P);
		for f in l[1]:
			if (f.endswith(".py")):
				Processed += 1;

				Recon_Concat_Variables(Python.Recon.Get.Variables(f"{P}/{f}"));
				Semicolons += Python.Recon.Get.Semicolon(f"{P}/{f}");
				Fors += Python.Recon.Get.Fors(f"{P}/{f}");
				Whitespaces += Python.Recon.Get.Whitespaces(f"{P}/{f}");
				Spacings += Python.Recon.Get.Spacings(f"{P}/{f}");

		for f in l[0]: Recon_Recursive(f"{P}/{f}");



	def Recon_Concat_Variables(V: dict[str, Type.Recon_Variable]) -> None:
		global Variables;
		for key in V.keys():
			if (not key in Variables.keys()): Variables[key] = V[key];
			else:
				for func in V[key]["Count"].keys():
					if (func in Variables[key]["Count"]): Variables[key]["Count"][func] += V[key]["Count"][func];
					else: Variables[key]["Count"][func] = V[key]["Count"][func];
				for t in V[key]["Type"]: Variables[key]["Type"].add(t);






	for w in Ogata["Watch"]: Recon_Recursive(f"{w}");

	for var in Variables.items():
		if (var[1]["Temporary"]): continue;
		if (len(var[1]["Type"]) == 0): Errors.append(f"{var[0]}: Undefined Type! \n{Culprit(var[1])}");
		if (len(var[1]["Type"]) > 1): Errors.append(f"{var[0]}: Type redefined {len(var[1]['Type'])} times! ({', '.join(var[1]['Type'])})\n{Culprit(var[1])}");
		for func in var[1]["Count"].keys():
			if (var[1]["Constant"] and var[1]["Count"][func] > 1): Errors.append(f"{var[0]}: Constant redefined {var[1]["Count"]} times!\n{Culprit(var[1])}");

		for t in var[1]["Type"]:
			if ("Any" in t): Warnings.append(f"{var[0]}: Type \"{t}\" contains \"Any\" which is discouraged.\n{Culprit(var[1])}");

	for e in Semicolons: Errors.append(f"Missing Semicolon!\n{Culprit(e)}");
	for e in Fors: Errors.append(f"Variable \"{e["Variable"]}\" used in For Loop isn't Lowercase!\n{Culprit(e)}");
	for e in Whitespaces: Errors.append(f"Spaces are used instead of tabs!\nFile {e['Path'][0]}, line {e['Line'][0]}");
	for e in Spacings: Errors.append(f"Bad spacing: Must be 0, 3, 5, 8 or 10 linebreaks long, got {e['String'][0]}.\nFile {e['Path'][0]}, line {e['Line'][0]}");

	for warning in Warnings: Log.Warning(warning);
	for error in Errors: Log.Error(error);

	header: str = f"Ogata processed {Processed} files in {Time.Elapsed_String(Time.Get_Unix(True) - Processed_Unix, Show_Until=-2)}:";
	if (len(Errors) > 0):
		Log.Critical(f"{header} {len(Errors)} Errors - {len(Warnings)} Warnings");
		exit(1);

	if (len(Warnings) > 0):
		Log.Error(f"{header} {len(Warnings)} Warnings");
		exit(0);

	Log.Info(f"{header} No errors!");
	return True;





if (__name__ == "__main__"):
	TSN_Abstracter.App_Init(True);
	Execute();