class LR35902():

    def __init__(self, bus):
        "Initializing registers and connecting the CPU to the bus."

        self.reg_high = {"B":"BC", "D":"DE", "H":"HL", "A":"AF"}
        self.reg_low = {"C":"BC", "E":"DE", "L":"HL", "F":"AF"}
        self.reg = {"BC":0x0, "DE":0x0, "HL":0x0, "AF":0x0, "PC":0x0, "SP": 0x0}
        self.flags = {"z" : 7, "n" : 6, "h" : 5, "c" : 4}
        self.bus = bus
        self.cycle = 0


    def getreg(self, entry):

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
    


    def setflags(self, z, n, h, c):

        args = [z, n, h, c]
        argnum = 0
        for flag in self.flags:
            if args[argnum] == None:
                argnum += 1
                continue
            value = int(args[argnum])
            if value > 0x1:
                raise ValueError(f"Value must be boolean: {hex(value)} ({bin(value)}) > 0x1")
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
    


    def LD(self, a, b, inc = 0, c = "None"):
        "Sets memory in a to memory in b and increments one of them depending on the argument."
        args = (a,b)
        
        match args:
            case 



    def LDH(self, n, ord = 1):
        "Adds value at location 0xFF00 + n in memory to registry entry A or the reverse operation depending on the argument."
        if ord:
            self.bus.write(0xFF00 + n, self.getreg("A"))
        else:
            self.setreg("A", self.bus.read(0xFF00 + n))



    """
    Below are the mathematical commands for the LR35902 CPU.
    """

    

    def ADC(self, n):
        "Adds the integer n plus the carry bit C to registry entry A."
        A = self.getreg("A")
        C = self.getreg("C")
        result = A + n + C
        self.setreg("A", result)
        self.setflags(result == 0, 0, ((A & 0xF) + (n & 0xF) + C) > 0xF, result > 0xFF)



    def SUB(self, n):
        "Subtracts the integer n from registry entry A."
        A = self.getreg("A")
        result = A - n
        self.setreg("A", result)
        self.setflags(result == 0, 1,  (A & 0xF) < (n & 0xF), result < 0)
    


    def SBC(self, n):
        "Subtracts the integer n and the carry bit C from registry entry A."
        A = self.getreg("A")
        C = self.getreg("C")
        result = A - (n + C)
        self.setreg("A", result)
        self.setflags(result == 0, 1,  (A & 0xF) < (n & 0xF), result < 0)



    def AND(self, n):
        "Logical bitwise and with registry entry A and integer n, result stored in A"
        result = n & self.getreg("A")
        self.setreg("A", result)
        self.setflags(result == 0, 0, 1, 0)



    def OR(self, n):
        "Logical bitwise or with registry entry A and integer n, result stored in A"
        result = n | self.getreg("A")
        self.setreg("A", result)
        self.setflags(result == 0, 0, 0, 0)



    def XOR(self, n):
        "Logical bitwise xor with registry entry A and integer n, result stored in A"
        result = n ^ self.getreg("A")
        self.setreg("A", result)
        self.setflags(result == 0, 0, 0, 0)
    


    def CP(self, n):
        "Compares integer n to registry entry A by calculating A - n and sets the flags according to the result."
        A = self.getreg("A")
        result = A - n
        self.setflags(result == 0, 1, (A & 0xF) < (n & 0xF), result < 0)



    def INC(self, r):
        "Increments registry r and sets the flags accordingly."
        R = self.getreg(r)
        result = R + 1
        self.setreg(result)
        if r in self.reg_low or self.reg_high:
            self.setflags(result == 0, 0, (result & 0xF) == 0x00, None)


    
    def DEC(self, r):
        "Increments registry r and sets the flags accordingly."
        R = self.getreg(r)
        result = R - 1
        self.setreg(r, result)
        if r in self.reg_low or self.reg_high:
            self.setflags(result == 0, 1, (R & 0xF) < (1 & 0xF), None)



    def ADD(self, r, n):
        "Adds value n to registry entry r."
        R = self.getreg(r)
        result = R + n if type(n) == int else R + self.getreg(n)
        if r == "A":
            self.setflags(result == 0, 0, (R & 0xF) + (n & 0xF) > 0xF, (result & 0x100) != 0)
        elif r == "HL":
            self.setflags(None, 0, (R & 0xFFF) + (n & 0xFFF) > 0xFFF, (result & 0x10000) != 0)
        elif r == "SP":
            self.setflags(0, 0, ((R ^ n ^ (result & 0xFFFF)) & 0x10) == 0x10, ((R ^ n ^ (result & 0xFFFF)) & 0x100) == 0x100)
        else:
            raise ValueError(f"Invalid registry entry: {r}")
        self.setreg(r, result)

    

    def SWAP(self, r):
        "Swaps the upper and lower nibble of register entry r."
        R = self.getreg(r)
        result = ((R & 0xF) << 4) | ((R & 0xF0) >> 4)
        self.setreg(r, result)
        self.setflags(result == 0, 0, 0, 0)



    def DAA(self):
        "Decimal adjusts register A."
        A = self.getreg("A")
        n = self.getreg("n")
        h = self.getreg("h")
        c = self.getreg("c")
        low = A & 0xF
        corr = 0

        if h or (not n and low > 0x9):
            corr |= 0x06

        if c or (not n and A > 0x9F):
            corr |= 0x60

        
        A += -corr if n else corr

        self.setreg("A", A)
        self.setflags(A == 0, None, 0, ((corr << 2) & 0x100) != 0)

    

    def CPL(self):
        "Sets register entry A to its complement."
        A = self.getreg("A")
        result = A ^ 0xFF
        self.setreg("A", result)
        self.setflags(None, 1, 1, None)
    


    def CCF(self):
        "Sets register flag C to its complement."
        C = self.getreg("c")
        result = C ^ 0x1
        self.setflags(None, 0, 0, result)



    def SCF(self):
        "Sets the carry flag C"
        self.setflags(None, 0, 0, 1)

    

    def readopcode(opcode):
        match opcode:

            case 0x00:
                NOP()
                self.cycle = 4

            case 0x01:
                LD("BC", )
                self.cycle = 4