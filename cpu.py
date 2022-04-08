class LR35902():

    def __init__(self, bus):
        "Initializing registers and connecting the CPU to the bus."
        self.reg_low = {"C":"BC", "E":"DE", "L":"HL", "F":"AF"}
        self.reg_high = {"B":"BC", "D":"DE", "H":"HL", "A":"AF"}
        self.reg = {"BC":0x0, "DE":0x0, "HL":0x0, "AF":0xFEFF, "PC":0x0, "SP": 0x0}
        self.flags = {"z" : 7, "n" : 6, "h" : 5, "c" : 4}
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
            value %= 0x100
            self.reg[self.reg_high[entry]] = (self.reg[self.reg_high[entry]] & 0xFF | (value << 0x8))
            

        elif entry in self.reg_low:
            value %= 0x100
            self.reg[self.reg_low[entry]] = ((self.reg[self.reg_low[entry]] >> 0x8) << 0x8 | value)

        else:
            if entry in self.reg:
                self.reg[entry] = value % 0x10000
            else:
                raise KeyError(f"Invalid register key: {entry}")
    
    def setFlags(self, z, n, h, c):
        args = [z, n, h, c]
        argnum = 0
        for flag in self.flags:
            if args[argnum] == None:
                argnum += 1
                continue
            value = int(args[argnum])
            if value > 0x1:
                raise ValueError(f"Value must be 0 or 1: {hex(value)} ({bin(value)}) > 0x1")
            f = self.getreg("F")
            flagbit = self.flags[flag]
            self.setreg("F", (f & ~(0x1 << flagbit)) | ((value << flagbit) & (0x1 << flagbit)))
            argnum += 1

    
    def fetch(self, addr):
        "Returns data at specified address in RAM."
        return self.bus.read(addr)

    def clock(self): #To be implemented
        "Updates the state of the CPU every clock-tick."
        while(True):
            if self.cycle == 0:
                self.setreg("PC", self.getreg("PC") + 1)


    """
    Below are the mathematical commands for the LR35902 CPU.
    """


    def LD(self, a, b, inc = 0, c = "None"): #To be implemented
        "Sets memory in a to memory in b and increments one of them depending on the argument."
        pass



    def LDH(self, n, ord = 1):
        "Adds value at location 0xFF00 + a in memory to registry entry A or the reverse operation depending on the argument."
        if ord:
            self.bus.write(0xFF00 + n, self.getreg("A"))
        else:
            self.setreg("A", self.bus.read(0xFF00 + n))



    def ADD(self, n):
        "Adds the value n to registry entry A."
        A = self.getreg("A")
        result = A + n
        self.setreg("A", result)
        self.setFlags(result == 0, 0, (n ^ A ^ result) & 0x10, (n ^ A ^ result) & 0x1000)

    

    def ADDC(self, n):
        "Adds the value n to registry entry A."
        A = self.getreg("A")
        C = self.getreg("C")
        result = A + n + C
        self.setreg("A", result)
        self.setFlags(result == 0, 0, (n ^ A ^ result) & 0x10, (n ^ A ^ result) & 0x1000)



    def AND(self, n):
        "Logical bitwise and with registry entry A and n, result stored in A"
        result = n & self.getreg("A")
        self.setreg("A", result)
        self.setFlags(result == 0, 0, 1, 0)



    def OR(self, n):
        "Logical bitwise or with registry entry A and n, result stored in A"
        result = n | self.getreg("A")
        self.setreg("A", result)
        self.setFlags(result == 0, 0, 0, 0)



    def XOR(self, n):
        "Logical bitwise xor with registry entry A and n, result stored in A"
        result = n ^ self.getreg("A")
        self.setreg("A", result)
        self.setFlags(result == 0, 0, 0, 0)
    


    def CP(self, n):
        "Compares n to registry entry A by calculating A - n and sets the flags according to the result."
        "Does not return anything."
        A = self.getreg("A")
        result = A - n
        self.setFlags(result == 0, 1, (A & 0xF) < (n & 0xF), result < 0)



    def INC(self, n):
        "Increments registry n and sets the flags accordingly."
        N = getreg(n)
        result = getreg(n) + 1
        self.setreg(result)
        if n in self.reg_low or self.reg_high:
            self.setFlags(result == 0, 0, (N ^ 0x1 ^ result) & 0x10, None)

    
    def DEC(self, n):
        "Increments registry n and sets the flags accordingly."
        N = getreg(n)
        result = getreg(n) - 1
        self.setreg(result)
        if n in self.reg_low or self.reg_high:
            self.setFlags(result == 0, 0, (N & 0xF) < (1 & 0xF), None)
