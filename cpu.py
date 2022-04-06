class LR35902():

    def __init__(self, bus):
        "Registry flags"
        self.reg_low = {"C":"BC", "E":"DE", "L":"HL", "F":"AF"}
        self.reg_high = {"B":"BC", "D":"DE", "H":"HL", "A":"AF"}
        self.reg = {"BC":0x0, "DE":0x0, "HL":0x0, "AF":0xAABB, "PC":0x0, "SP": 0x0}
        self.flags = {"z" : 0x7, "n" : 0x6, "h" : 0x5, "c" : 0x4}
        self.bus = bus
        self.cycle = 0

    def getreg(self, entry):
        "Fetching registry entries."
        if entry in self.reg_high:
            return self.reg[self.reg_high[entry]] >> 0x8

        elif entry in self.reg_low:
            return self.reg[self.reg_low[entry]] & 0xFF

        elif entry in self.flags:
            return self.reg["AF"] >> self.flags[entry] & 0x1

        else:
            if entry in self.reg:
                return self.reg[entry]
            else:
                raise KeyError(f"Invalid register key: {entry}")

    def setreg(self, entry, value):
        "Setting registry entries."
        if entry in self.reg_high:
            if value > 0xFF:
                raise ValueError(f"Value out of range: {hex(value)} ({bin(value)}) > 0xFF")
            self.reg[self.reg_high[entry]] = self.reg[self.reg_high[entry]] & 0xFF | (value<<8)

        elif entry in self.reg_low:
            if value > 0xFF:
                raise ValueError(f"Value out of range: {hex(value)} ({bin(value)}) > 0xFF")
            self.reg[self.reg_low[entry]] = (self.reg[self.reg_low[entry]] >> 0x8) <<8 | value

        elif entry in self.flags:
            if value > 0x1:
                raise ValueError(f"Value out of range: {hex(value)} ({bin(value)}) > 0x1")
            f = self.getreg("F")
            flag = self.flags[entry]
            self.setreg("F", (f & ~(1 << flag)) | ((value << flag) & (1 << flag)))

        else:
            if entry in self.reg:
                if value > 0xFFFF:
                    raise ValueError(f"Value out of range: {hex(value)} ({bin(value)}) > 0xFFFF")
                self.reg[entry] = value
            else:
                raise KeyError(f"Invalid register key: {entry}")
    
    def fetch(self, addr):
        "Fetches data at specified address in RAM."
        return self.bus.read(addr)

    def clock(self): #To be implemented
        "Updates the state of the CPU every clock-tick."
        if not self.cycle:
            self.setreg("PC", self.getreg("PC") + 1)

    def LD(self, a, b, inc = 0, c = "None"): #To be implemented
            "Sets memory in a to memory in b and sometimes increments one of them."
            pass
            """
            a = b
            if inc:
                c += inc
            """

    def LDH(self, a, ord = 1):
        "Adds value at location 0xFF00 + a in memory to registry entry A or the reverse operation depending on the argument."
        if ord:
            self.bus.write(0xFF00 + a, self.getreg("A"))
        else:
            self.setreg("A", self.bus.read(0xFF00 + a))

    def ADD(self, a):
        "Adds the value a to registry entry A."
        self.setreg(self.getreg("A") + a)
