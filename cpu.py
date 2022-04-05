class LR35902():

    def __init__(self):
        self.reg_low = {"F":"AF", "C":"BC", "E":"DE", "L":"HL"}
        self.reg_high = {"A":"AF", "B":"BC", "D":"DE", "H":"HL"}
        self.reg = {"AF":0xAABB, "BC":0x0, "DE":0x0, "HL":0x0, "PC":0x0, "SP": 0x0}
        self.flags = {"z" : 7, "n" : 6, "h" : 5, "c" : 4}

    def getreg(self, entry):
        if entry in self.reg_high:
            return self.reg[self.reg_high[entry]] >> 8

        elif entry in self.reg_low:
            return self.reg[self.reg_low[entry]] & 0xFF

        elif entry in self.flags:
            return self.reg["AF"] >> self.flags[entry] & 1

        else:
            if entry in self.reg:
                return self.reg[entry]
            else:
                raise KeyError(f"Invalid register key: {entry}")


test = LR35902()


print(hex(test.getreg("Q")))