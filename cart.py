import sys
import struct
from array import array

Licensee_Codes = {
	    0x00 : "None",
	    0x01 : "Nintendo R&D1",
	    0x08 : "Capcom",
	    0x13 : "Electronic Arts",
	    0x18 : "Hudson Soft",
	    0x19 : "b-ai",
	    0x20 : "kss",
	    0x22 : "pow",
	    0x24 : "PCM Complete",
	    0x25 : "san-x",
	    0x28 : "Kemco Japan",
	    0x29 : "seta",
	    0x30 : "Viacom",
	    0x31 : "Nintendo",
	    0x32 : "Bandai",
	    0x33 : "Ocean/Acclaim",
	    0x34 : "Konami",
	    0x35 : "Hector",
	    0x37 : "Taito",
	    0x38 : "Hudson",
	    0x39 : "Banpresto",
	    0x41 : "Ubi Soft",
	    0x42 : "Atlus",
	    0x44 : "Malibu",
	    0x46 : "angel",
	    0x47 : "Bullet-Proof",
	    0x49 : "irem",
	    0x50 : "Absolute",
	    0x51 : "Acclaim",
	    0x52 : "Activision",
	    0x53 : "American sammy",
	    0x54 : "Konami",
	    0x55 : "Hi tech entertainment",
	    0x56 : "LJN",
	    0x57 : "Matchbox",
	    0x58 : "Mattel",
	    0x59 : "Milton Bradley",
	    0x60 : "Titus",
	    0x61 : "Virgin",
	    0x64 : "LucasArts",
	    0x67 : "Ocean",
	    0x69 : "Electronic Arts",
	    0x70 : "Infogrames",
	    0x71 : "Interplay",
	    0x72 : "Broderbund",
	    0x73 : "sculptured",
	    0x75 : "sci",
	    0x78 : "THQ",
	    0x79 : "Accolade",
	    0x80 : "misawa",
	    0x83 : "lozc",
	    0x86 : "Tokuma Shoten Intermedia",
	    0x87 : "Tsukuda Original",
	    0x91 : "Chunsoft",
	    0x92 : "Video system",
	    0x93 : "Ocean/Acclaim",
	    0x95 : "Varie",
	    0x96 : "Yonezawa/s’pal",
	    0x97 : "Kaneko",
	    0x99 : "Pack in soft",
	    0xA4 : "Konami (Yu-Gi-Oh!)"
	}


class Cartridge():

	def __init__(self, ROM):
		self.data = array("B", ROM.read())
		self.size = len(self.data) #bytes
		self.header = 0x0100
	
	def displaydata(self, ran = None):
		"Display cartridge data for debugging."
		if ran is None:
			ran = [0, len(self.data)]
		datahex = []
		for i in range(ran[0], ran[1]):
			datahex.append(format(self.data[i], 'X'))
		print(datahex)

	def getmetadata(self): #To be implemented
		"Returns the metadata of the ROM."
		pass
		