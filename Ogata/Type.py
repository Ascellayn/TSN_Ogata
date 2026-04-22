from typing import TypedDict, Optional; # pyright: ignore[reportUnusedImport]





class Ogata_Config(TypedDict):
	_Version: list[int] | tuple[int, ...];
	Watch: list[str];





class Recon_Base(TypedDict):
	Path: list[str];
	Line: list[int];
	String: list[str];

class Recon_Variable(Recon_Base):
	Count: dict[str, int];
	Type: set[str];
	Constant: bool;
	Temporary: bool;

class Recon_For(Recon_Base):
	Variable: str;





__all__: list[str] = [
	"Ogata_Config",
	"Recon_Base", "Recon_Variable"
];