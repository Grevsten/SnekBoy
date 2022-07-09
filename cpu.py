class LR35902():

    def __init__(self, bus):
        "Initializing registers and connecting the CPU to the bus."

        self.reg_high = {"B":"BC", "D":"DE", "H":"HL", "A":"AF"}
        self.reg_low = {"C":"BC", "E":"DE", "L":"HL", "F":"AF"}
        self.reg = {"BC":0x0000, "DE":0x0000, "HL":0x0000, "AF":0x0000, "PC":0x0000, "SP": 0x0000}
        self.flags = {"z" : 7, "n" : 6, "h" : 5, "c" : 4}
        self.bus = bus
        self.cycle = 0 # Clock cycles
        self.prefix = 0


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



    def fetch(self):
        addr = self.getreg("PC")
        instruction = self.bus.read(addr)
        if self.prefix:
            self.readprefixedopcode(instruction)
            self.prefix = 0
        else:
            self.readopcode(instruction)
    


    def getbyteatpc(self):
        PC = self.getreg("PC")
        self.INC("PC")
        value = self.bus.read(PC)
        return value



    def getwordatpc(self):
        low = self.getbyteatpc()
        high = self.getbyteatpc()
        value =  low | high << 8
        return value
    


    def getsignedbyteatpc(self):
        s8 = self.getbyteatpc()
        if s8 >> 7:
            return -(s8 | 0x7F)
        else:
            return s8 | 0x7F
        


    def popstack(self, n):
        value = n if type(n) == int else self.getreg(n)
        low = self.bus.read(self.getreg("SP"))
        self.INC("SP")
        high = self.bus.read(self.getreg("SP"))
        self.INC("SP")
        value = low | high << 8
        if n in self.reg_high or n in self.reg_low or n in self.reg:
            self.setreg(n, value)
        else:
            self.bus.write(n, value)
    


    def pushstack(self, n):
        value = n if type(n) == int else self.getreg(n)
        self.DEC("SP")
        self.bus.write(self.getreg("SP"), value | 0xFF00)
        self.DEC("SP")
        self.bus.write(self.getreg("SP"), value | 0xFF)



    def clock(self): #To be implemented
        "Updates the state of the CPU every clock-tick."
        while(True):
            if self.cycle == 0:

                self.INC("PC")

                self.fetch()

    

    """Below are the opcodes for the LR35902 processor."""

    def LD(self, A, B):
        "Sets memory in A to value B."

        if B in self.reg_high or B in self.reg_low or B in self.reg:
            B = self.getreg(B)
        
        if A in self.reg_high or A in self.reg_low or A in self.reg:
            self.setreg(A, B)
        else:
            self.bus.write(A, B)
    


    def LDHL(self):
        SP = self.getreg("SP")
        s8 = self.getsignedbyteatpc()
        result = SP + s8
        self.setreg("HL", result)
        self.setflags(0, 0, ((SP ^ s8 ^ (result & 0xFFFF)) & 0x10) == 0x10, ((SP ^ s8 ^ (result & 0xFFFF)) & 0x100) == 0x10)
    


    def LDC(self, ord):
        c = self.getreg("c")
        if ord:
            self.bus.write(0xFF00 + c, self.getreg("A"))
        else:
            self.setreg("A", self.bus.read(0xFF00 + c))
    


    def LDI(self, A, B):
        "Sets memory in A to value B and increments HL."
        self.LD(A, B)
        HL = self.getreg("HL")
        self.setreg("HL", HL + 1)
    


    def LDD(self, A, B):
        "Sets memory in A to value B and decrements HL."
        self.LD(A, B)
        HL = self.getreg("HL")
        self.setreg("HL", HL - 1)



    def LDH(self, ord):
        "Adds value at location 0xFF00 plus immediate byte to the accumulator or the reverse operation depending on the argument."
        a8 = self.getbyteatpc()
        if ord:
            self.bus.write(0xFF00 + a8, self.getreg("A"))
        else:
            self.setreg("A", self.bus.read(0xFF00 + a8))



    def PUSH(self, reg):
        "Pushes registry onto the stack."
        self.pushstack(reg)
    


    def POP(self, reg):
        "Pops value off the stack and writes it to registry."
        self.popstack(reg)


    
    def ADC(self, n):
        "Adds the integer n plus the carry bit to the accumulator."
        A = self.getreg("A")
        c = self.getreg("c")
        N = n if type(n) == int else self.getreg(n)
        result = A + N + c
        self.setreg("A", result)
        self.setflags(result == 0, 0, ((A & 0xF) + (N & 0xF) + c) > 0xF, result > 0xFF)



    def SUB(self, n):
        "Subtracts the integer n from the accumulator."
        A = self.getreg("A")
        N = n if type(n) == int else self.getreg(n)
        result = A - N
        self.setreg("A", result)
        self.setflags(result == 0, 1,  (A & 0xF) < (N & 0xF), result < 0)
    


    def SBC(self, n):
        "Subtracts the integer n and the carry bit C from the accumulator."
        A = self.getreg("A")
        c = self.getreg("c")
        N = n if type(n) == int else self.getreg(n)
        result = A - (N + c)
        self.setreg("A", result)
        self.setflags(result == 0, 1,  (A & 0xF) < (N & 0xF), result < 0)



    def AND(self, n):
        "Logical bitwise and with the accumulator and integer n, result stored in the accumulator."
        N = n if type(n) == int else self.getreg(n)
        result = N & self.getreg("A")
        self.setreg("A", result)
        self.setflags(result == 0, 0, 1, 0)



    def OR(self, n):
        "Logical bitwise or with the accumulator and integer n, result stored in the accumulator."
        N = n if type(n) == int else self.getreg(n)
        result = N | self.getreg("A")
        self.setreg("A", result)
        self.setflags(result == 0, 0, 0, 0)



    def XOR(self, n):
        "Logical bitwise xor with the accumulator and integer n, result stored in the accumulator"
        N = n if type(n) == int else self.getreg(n)
        result = N ^ self.getreg("A")
        self.setreg("A", result)
        self.setflags(result == 0, 0, 0, 0)
    


    def CP(self, n):
        "Compares integer n to the accumulator by calculating A - n and sets the flags according to the result."
        A = self.getreg("A")
        N = n if type(n) == int else self.getreg(n)
        result = A - N
        self.setflags(result == 0, 1, (A & 0xF) < (N & 0xF), result < 0)



    def INC(self, r):
        "Increments registry r and sets the flags accordingly."
        if r in self.reg or r in self.reg_low or r in self.reg_high:
            R = self.getreg(r)
            result = R + 1
            self.setreg(r, result)
            if r in self.reg_low or self.reg_high:
                self.setflags(result == 0, 0, (result & 0xF) == 0x00, None)
        else:
            R = self.bus.read(r)
            result = R + 1
            self.bus.write(r, result)


    
    def DEC(self, r):
        "Increments registry r and sets the flags accordingly."
        if r in self.reg or r in self.reg_low or r in self.reg_high:
            R = self.getreg(r)
            result = R - 1
            self.setreg(r, result)
            if r in self.reg_low or self.reg_high:
                self.setflags(result == 0, 1, (R & 0xF) < (1 & 0xF), None)
        else:
            R = self.bus.read(r)
            result = R - 1
            self.bus.write(r, result)



    def ADD(self, r, n):
        "Adds value n to registry entry r."
        R = self.getreg(r)
        N = n if type(n) == int else self.getreg(n)
        result = R + N 
        if r == "A":
            self.setflags(result == 0, 0, (R & 0xF) + (N & 0xF) > 0xF, (result & 0x100) != 0)
        elif r == "HL":
            self.setflags(None, 0, (R & 0xFFF) + (N & 0xFFF) > 0xFFF, (result & 0x10000) != 0)
        elif r == "SP":
            self.setflags(0, 0, ((R ^ N ^ (result & 0xFFFF)) & 0x10) == 0x10, ((R ^ N ^ (result & 0xFFFF)) & 0x100) == 0x100)
        else:
            raise ValueError(f"Invalid registry entry: {r}")
        self.setreg(r, result)

    

    def SWAP(self, n):
        "Swaps the upper and lower nibble of value n."
        N = self.bus.read(n) if type(n) == int else self.getreg(n)
        result = (( N & 0xF) << 4) | (( N & 0xF0) >> 4)
        if n in self.reg_high or n in self.reg_low:
            self.setreg(n, result & 0xFF)
        else:
            self.bus.write(n, result & 0xFF)
        self.setflags(result == 0, 0, 0, 0)



    def DAA(self):
        "Decimal adjusts the accumulator."
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
        "Sets the accumulator to its complement."
        A = self.getreg("A")
        result = A ^ 0xFF
        self.setreg("A", result)
        self.setflags(None, 1, 1, None)
    


    def CCF(self):
        "Sets the carry flag to its complement."
        c = self.getreg("c")
        result = c ^ 0x1
        self.setflags(None, 0, 0, result)



    def SCF(self):
        "Sets the carry flag."
        self.setflags(None, 0, 0, 1)
    


    def NOP(self):
        "Performs no operation."
        pass
    


    def HALT(self):
        "Powers down CPU until an interrupt is triggered."
        pass



    def STOP(self):
        "Halts the CPU and screen until a button is pressed."
        pass



    def DI(self):
        "Disables interuppts after next instruction is executed."
        pass
    


    def EI(self):
        "Enables interuppts after next instruction is executed."
        pass



    def RLCA(self):
        "Rotates the accumulator one step to the left and sets the carry flag to old bit 7."
        A = self.getreg("A")
        result = ((A << 1)|(A >> 7)) & 0xFF
        self.setreg("A", result)
        self.setflags(result == 0, None, None, A >> 0x7 & 0x1)
    


    def RLA(self):
        "Rotates the accumulator one step to the left through the carry flag."
        A = self.getreg("A")
        c = self.getreg("c")
        cA = (c << 8) | A
        result = ((cA << 1)|(cA >> 8)) & 0x1FF
        self.setreg("A", result & 0xFF)
        self.setflags(result & 0xFF == 0, None, None, result >> 0x8 & 0x1)

    

    def RRCA(self):
        "Rotates the accumulator one step to the right and sets carry flag to old bit 0."
        A = self.getreg("A")
        result = (A >> 1)|((A << 7) & 0xFF)
        self.setreg("A", result)
        self.setflags(result == 0, None, None, A & 0x1)    



    def RRA(self):
        "Rotates the accumulator one step to the right through the carry flag."
        A = self.getreg("A")
        c = self.getreg("c")
        Ac = (A << 1) | c
        result = (Ac >> 1)|((Ac << 8) & 0x1FF)
        self.setreg("A", result >> 1)
        self.setflags(result >> 1 == 0, None, None, result & 0x1)
    


    def RLC(self, n):
        "Rotates value n one step to the left and sets carry flag to old bit 7."
        N = self.bus.read(n) if type(n) == int else self.getreg(n)
        result = (N >> 1)|((N << 7) & 0xFF)
        if n in self.reg_high or n in self.reg_low:
            self.setreg(n, result & 0xFF)
        else:
            self.bus.write(n, result & 0xFF)
        self.setflags(result & 0xFF == 0, None, None, N >> 0x7 & 0x1)
    


    def RL(self, n):
        "Rotates value n one step to the left through the carry flag."
        N = self.bus.read(n) if type(n) == int else self.getreg(n)
        c = self.getreg("c")
        cN = (c << 8) | N
        result = ((cN << 1)|(cN >> 8)) & 0x1FF
        if n in self.reg_high or n in self.reg_low:
            self.setreg(n, result & 0xFF)
        else:
            self.bus.write(n, result & 0xFF)
        self.setflags(result & 0xFF == 0, 0, 0, result >> 0x8 & 0x1)
    


    def RRC(self, n):
        "Rotates value n one step to the right and sets carry flag to old bit 0."
        N = self.bus.read(n) if type(n) == int else self.getreg(n)
        result = (N >> 1)|((N << 7) & 0xFF)
        if n in self.reg_high or n in self.reg_low:
            self.setreg(n, result)
        else:
            self.bus.write(n, result)
        self.setflags(result == 0, 0, 0, N & 0x1)
    


    def RR(self, n):
        "Rotates value n one step to the right through the carry flag."
        N = self.bus.read(n) if type(n) == int else self.getreg(n)
        c = self.getreg("c")
        Nc = (N << 1) | c
        result = (Nc >> 1)|((Nc << 8) & 0x1FF)
        if n in self.reg_high or n in self.reg_low:
            self.setreg(n, result >> 1)
        else:
            self.bus.write(n, result >> 1)
        self.setflags(result >> 1 == 0, 0, 0, result & 0x1)
    


    def SLA(self, n):
        "Rotates value n one step to the left through the carry flag. Least significant bit of n set to zero."
        N = self.bus.read(n) if type(n) == int else self.getreg(n)
        c = self.getreg("c")
        cN = (c << 8) | N
        result = ((cN << 1)|(cN >> 8)) & 0x1FF
        result &= 0x1FE
        if n in self.reg_high or n in self.reg_low:
            self.setreg(n, result & 0xFF)
        else:
            self.bus.write(n, result & 0xFF)
        self.setflags(result & 0xFF == 0, 0, 0, result >> 0x8 & 0x1)
    


    def SRA(self, n):
        "Rotates value n one step to the right through the carry flag. Most significant bit unchanged."
        N = self.bus.read(n) if type(n) == int else self.getreg(n)
        c = self.getreg("c")
        Nc = (N << 1) | c
        result = (Nc >> 1)|((Nc << 8) & 0x1FF)
        if N & 0x100 == 0x100:
            result |= 0x100
        else:
            result &= 0xFF
        if n in self.reg_high or n in self.reg_low:
            self.setreg(n, result >> 1)
        else:
            self.bus.write(n, result >> 1)
        self.setflags(result >> 1 == 0, 0, 0, result & 0x1)
    


    def SRL(self, n):
        "Rotates value n one step to the right through the carry flag. Most significant bit unset."
        N = self.bus.read(n) if type(n) == int else self.getreg(n)
        c = self.getreg("c")
        Nc = (N << 1) | c
        result = (Nc >> 1)|((Nc << 8) & 0x1FF)
        result &= 0xFF
        if n in self.reg_high or n in self.reg_low:
            self.setreg(n, result >> 1)
        else:
            self.bus.write(n, result >> 1)
        self.setflags(result >> 1 == 0, 0, 0, result & 0x1)
    


    def BIT(self, b, r):
        "Checks bit b in value r and sets flags accordingly."
        R = self.bus.read(r) if type(r) == int else self.getreg(r)
        bit = (R >> b) & 0x1
        self.setflags(not bit, 0, 1, None)
    


    def SET(self, b, r):
        "Sets bit b in value r."
        R = self.bus.read(r) if type(r) == int else self.getreg(r)
        result = R | (0x1 << b)
        if r in self.reg_high or r in self.reg_low:
            self.setreg(r, result)
        else:
            self.bus.write(r, result)



    def RES(self, b, r):
        "Resets bit b in value r."
        R = self.bus.read(r) if type(r) == int else self.getreg(r)
        result = R & ~(1 << b)
        if r in self.reg_high or r in self.reg_low:
            self.setreg(r, result)
        else:
            self.bus.write(r, result)


    def JP(self, cond = True, u16 = None):
        if u16 is None:
            u16 = self.getwordatpc()
        if cond:
            self.setreg("PC", u16)
    


    def JR(self, cond = True):
        "Adds immediate signed byte to the current address in the programme counter."
        s8 = self.getsignedbyteatpc()
        if cond:
            PC = self.getreg("PC")
            result = s8 + PC
            self.setreg("PC", result)

    

    def CALL(self, cond = True):
        u16 = self.getwordatpc()
        if cond:
            self.pushstack(self.getreg("PC"))
            self.setreg("PC", u16)
    


    def RST(self, u8):
        self.pushstack(self.getreg("PC"))
        self.setreg("PC", u8)



    def RET(self, cond = True):
        if cond:
            self.popstack("PC")
    


    def RETI(self):
        self.RET()
        self.EI()
    


    def readopcode(self,byte):

        match byte:

            case 0x00:
                self.NOP()
                self.cycle = 4

            case 0x01:
                self.LD("BC", self.getwordatpc())
                self.cycle = 12

            case 0x02:
                self.LD(self.getreg("BC"), "A")
                self.cycle = 8
            
            case 0x03:
                self.INC("BC")
                self.cycle = 8

            case 0x04:
                self.INC("B")
                self.cycle = 4

            case 0x05:
                self.DEC("B")
                self.cycle = 4

            case 0x06:
                self.LD(self.getbyteatpc(), "B")
                self.cycle = 8

            case 0x07:
                self.RLCA()
                self.cycle = 4
            
            case 0x08:
                self.LD(self.getwordatpc(), self.getreg("SP"))
                self.cycle = 20

            case 0x09:
                self.ADD("HL", "BC")
                self.cycle = 8

            case 0x0A:
                self.LD("A", self.bus.read(self.getreg("BC")))
                self.cycle = 8

            case 0x0B:
                self.DEC("BC")
                self.cycle = 8
            
            case 0x0C:
                self.INC("C")
                self.cycle = 4
            
            case 0x0D:
                self.DEC("C")
                self.cycle = 4
            
            case 0x0E:
                self.LD(self.getbyteatpc(), "C")
                self.cycle = 8
            
            case 0x0F:
                self.RRCA()
                self.cycle = 4
            
            case 0x10:
                self.STOP()
                self.cycle = 4
            
            case 0x11:
                self.LD("DE", self.getwordatpc())
                self.cycle = 12
            
            case 0x12:
                self.LD(self.getreg("DE"), "A")
                self.cycle = 8
            
            case 0x13:
                self.INC("DE")
                self.cycle = 8
            
            case 0x14:
                self.INC("D")
                self.cycle = 4

            case 0x15:
                self.DEC("D")
                self.cycle = 4
            
            case 0x16:
                self.LD(self.getbyteatpc(), "D")
                self.cycle = 8

            case 0x17:
                self.RLA()
                self.cycle = 4
            
            case 0x18:
                self.JR()
                self.cycle = 12
            
            case 0x19:
                self.ADD("HL", "DE")
                self.cycle = 8

            case 0x1A:
                self.LD("A", self.bus.read(self.getreg("DE")))
                self.cycle = 8
            
            case 0x1B:
                self.DEC("DE")
                self.cycle = 8
            
            case 0x1C:
                self.INC("E")
                self.cycle = 4
            
            case 0x1D:
                self.DEC("E")
                self.cycle = 4
            
            case 0x1E:
                self.LD(self.getbyteatpc(), "E")
                self.cycle = 8
            
            case 0x1F:
                self.RRA()
                self.cycle = 4
            
            case 0x20:
                self.JR(not self.getreg("z"))
                self.cycle = 8
            
            case 0x21:
                self.LD("DE", self.getwordatpc())
                self.cycle = 12
            
            case 0x22:
                self.LDI(self.getreg("HL"), "A")
                self.cycle = 8
            
            case 0x23:
                self.INC("HL")
                self.cycle = 8
            
            case 0x24:
                self.INC("H")
                self.cycle = 4
            
            case 0x25:
                self.DEC("H")
                self.cycle = 4
            
            case 0x26:
                self.LD(self.getbyteatpc(), "H")
                self.cycle = 8
            
            case 0x27:
                self.DAA()
                self.cycle = 4
            
            case 0x28:
                self.JR(self.getreg("z"))
                self.cycle = 12
            
            case 0x29:
                self.ADD("HL", "HL")
                self.cycle = 8
            
            case 0x2A:
                self.LDI("A", self.bus.read(self.getreg("HL")))
                self.cycle = 8
            
            case 0x2B:
                self.DEC("HL")
                self.cycle = 8
            
            case 0x2C:
                self.INC("L")
                self.cycle = 4
            
            case 0x2D:
                self.DEC("L")
                self.cycle = 4
            
            case 0x2E:
                self.LD(self.getbyteatpc(), "L")
                self.cycle = 8
            
            case 0x2F:
                self.CPL()
                self.cycle = 4
            
            case 0x30:
                self.JR(not self.getreg("c"))
                self.cycle = 12
            
            case 0x31:
                self.LD("SP", self.getwordatpc())
                self.cycle = 12
            
            case 0x32:
                self.LDD(self.getreg("HL"), "A")
                self.cycle = 8
            
            case 0x33:
                self.INC("SP")
                self.cycle = 8
            
            case 0x34:
                self.INC(self.getreg("HL"))
                self.cycle = 12
            
            case 0x35:
                self.DEC(self.getreg("HL"))
                self.cycle = 12
            
            case 0x36:
                self.LD(self.getbyteatpc(), self.bus.read(self.getreg("HL")))
                self.cycle = 12
            
            case 0x37:
                self.SCF()
                self.cycle = 4
            
            case 0x38:
                self.JR(self.getreg("c"))
                self.cycle = 12
            
            case 0x39:
                self.ADD("HL", "SP")
                self.cycle = 8
            
            case 0x3A:
                self.LDD("A", self.bus.read(self.getreg("HL")))
                self.cycle = 8
            
            case 0x3B:
                self.DEC("SP")
                self.cycle = 8
            
            case 0x3C:
                self.INC("A")
                self.cycle = 4
            
            case 0x3D:
                self.DEC("A")
                self.cycle = 4
            
            case 0x3E:
                self.LD(self.getbyteatpc(), "A")
                self.cycle = 8
            
            case 0x3F:
                self.CCF()
                self.cycle = 4
            
            case 0x40:
                self.LD("B", "B")
                self.cycle = 4
 
            case 0x41:
                self.LD("B", "C")
                self.cycle = 4
            
            case 0x42:
                self.LD("B", "D")
                self.cycle = 4
            
            case 0x43:
                self.LD("B", "E")
                self.cycle = 4
            
            case 0x44:
                self.LD("B", "H")
                self.cycle = 4
            
            case 0x45:
                self.LD("B", "L")
                self.cycle = 4
            
            case 0x46:
                self.LD("B", self.bus.read(self.getreg("HL")))
                self.cycle = 8
            
            case 0x47:
                self.LD("B", "A")
                self.cycle = 4
            
            case 0x48:
                self.LD("C", "B")
                self.cycle = 4
            
            case 0x49:
                self.LD("C", "C")
                self.cycle = 4
            
            case 0x4A:
                self.LD("C", "D")
                self.cycle = 4
            
            case 0x4B:
                self.LD("C", "E")
                self.cycle = 4
            
            case 0x4C:
                self.LD("C", "H")
                self.cycle = 4
            
            case 0x4D:
                self.LD("C", "L")
                self.cycle = 4
            
            case 0x4E:
                self.LD("C", self.bus.read(self.getreg("HL")))
                self.cycle = 8
            
            case 0x4F:
                self.LD("C", "A")
                self.cycle = 4
            
            case 0x50:
                self.LD("D", "B")
                self.cycle = 4
            
            case 0x51:
                self.LD("D", "C")
                self.cycle = 4
            
            case 0x52:
                self.LD("D", "D")
                self.cycle = 4
            
            case 0x53:
                self.LD("D", "E")
                self.cycle = 4
            
            case 0x54:
                self.LD("D", "H")
                self.cycle = 4
            
            case 0x55:
                self.LD("D", "L")
                self.cycle = 4
            
            case 0x56:
                self.LD("D", self.bus.read(self.getreg("HL")))
                self.cycle = 8
            
            case 0x57:
                self.LD("D", "A")
                self.cycle = 4
            
            case 0x58:
                self.LD("E", "B")
                self.cycle = 4
            
            case 0x59:
                self.LD("E", "C")
                self.cycle = 4
            
            case 0x5A:
                self.LD("E", "D")
                self.cycle = 4
            
            case 0x5B:
                self.LD("E", "E")
                self.cycle = 4
            
            case 0x5C:
                self.LD("E", "H")
                self.cycle = 4
            
            case 0x5D:
                self.LD("E", "L")
                self.cycle = 4
            
            case 0x5E:
                self.LD("E", self.bus.read(self.getreg("HL")))
                self.cycle = 8
            
            case 0x5F:
                self.LD("E", "A")
                self.cycle = 4
            
            case 0x60:
                self.LD("H", "B")
                self.cycle = 4
            
            case 0x61:
                self.LD("H", "C")
                self.cycle = 4
            
            case 0x62:
                self.LD("H", "D")
                self.cycle = 4
            
            case 0x63:
                self.LD("H", "E")
                self.cycle = 4
            
            case 0x64:
                self.LD("H", "H")
                self.cycle = 4
            
            case 0x65:
                self.LD("H", "L")
                self.cycle = 4
            
            case 0x66:
                self.LD("H", self.bus.read(self.getreg("HL")))
                self.cycle = 8
            
            case 0x67:
                self.LD("H", "A")
                self.cycle = 4
            
            case 0x68:
                self.LD("L", "B")
                self.cycle = 4
            
            case 0x69:
                self.LD("L", "C")
                self.cycle = 4
            
            case 0x6A:
                self.LD("L", "D")
                self.cycle = 4
            
            case 0x6B:
                self.LD("L", "E")
                self.cycle = 4
            
            case 0x6C:
                self.LD("L", "H")
                self.cycle = 4
            
            case 0x6D:
                self.LD("L", "L")
                self.cycle = 4
            
            case 0x6E:
                self.LD("L", self.bus.read(self.getreg("HL")))
                self.cycle = 8
            
            case 0x6F:
                self.LD("L", "A")
                self.cycle = 4
            
            case 0x70:
                self.LD(self.getreg("HL"), "B")
                self.cycle = 8
            
            case 0x71:
                self.LD(self.getreg("HL"), "C")
                self.cycle = 8
            
            case 0x72:
                self.LD(self.getreg("HL"), "D")
                self.cycle = 8
            
            case 0x73:
                self.LD(self.getreg("HL"), "E")
                self.cycle = 8
            
            case 0x74:
                self.LD(self.getreg("HL"), "H")
                self.cycle = 8
            
            case 0x75:
                self.LD(self.getreg("HL"), "L")
                self.cycle = 8
            
            case 0x76:
                self.LD(self.getreg("HL"), self.bus.read(self.getreg("HL")))
                self.cycle = 4
            
            case 0x77:
                self.LD(self.getreg("HL"), "A")
                self.cycle = 8
            
            case 0x78:
                self.LD("A", "B")
                self.cycle = 4
            
            case 0x79:
                self.LD("A", "C")
                self.cycle = 4
            
            case 0x7A:
                self.LD("A", "D")
                self.cycle = 4
            
            case 0x7B:
                self.LD("A", "E")
                self.cycle = 4
            
            case 0x7C:
                self.LD("A", "H")
                self.cycle = 4
            
            case 0x7D:
                self.LD("A", "L")
                self.cycle = 4
            
            case 0x7E:
                self.LD("A", self.bus.read(self.getreg("HL")))
                self.cycle = 8
            
            case 0x7F:
                self.LD("A", "A")
                self.cycle = 4

            case 0x80:
                self.ADD("A", "B")
                self.cycle = 4
            
            case 0x81:
                self.ADD("A", "C")
                self.cycle = 4
            
            case 0x82:
                self.ADD("A", "D")
                self.cycle = 4
            
            case 0x83:
                self.ADD("A", "E")
                self.cycle = 4
            
            case 0x84:
                self.ADD("A", "H")
                self.cycle = 4
            
            case 0x85:
                self.ADD("A", "L")
                self.cycle = 4
            
            case 0x86:
                self.ADD("A", self.bus.read(self.getreg("HL")))
                self.cycle = 8
            
            case 0x87:
                self.ADD("A", "A")
                self.cycle = 4
            
            case 0x88:
                self.ADC("B")
                self.cycle = 4
            
            case 0x89:
                self.ADC("C")
                self.cycle = 4
            
            case 0x8A:
                self.ADC("D")
                self.cycle = 4
            
            case 0x8B:
                self.ADC("E")
                self.cycle = 4
            
            case 0x8C:
                self.ADC("H")
                self.cycle = 4
            
            case 0x8D:
                self.ADC("L")
                self.cycle = 4
            
            case 0x8E:
                self.ADC(self.bus.read(self.getreg("HL")))
                self.cycle = 8
            
            case 0x8F:
                self.ADC("A")
                self.cycle = 4
            
            case 0x90:
                self.SUB("B")
                self.cycle = 4
            
            case 0x91:
                self.SUB("C")
                self.cycle = 4
            
            case 0x92:
                self.SUB("D")
                self.cycle = 4
            
            case 0x93:
                self.SUB("E")
                self.cycle = 4
            
            case 0x94:
                self.SUB("H")
                self.cycle = 4
            
            case 0x95:
                self.SUB("L")
                self.cycle = 4
            
            case 0x96:
                self.SUB(self.bus.read(self.getreg("HL")))
                self.cycle = 8
            
            case 0x97:
                self.SUB("A")
                self.cycle = 4
            
            case 0x98:
                self.SBC("B")
                self.cycle = 4
            
            case 0x99:
                self.SBC("C")
                self.cycle = 4
            
            case 0x9A:
                self.SBC("D")
                self.cycle = 4
            
            case 0x9B:
                self.SBC("E")
                self.cycle = 4
            
            case 0x9C:
                self.SBC("H")
                self.cycle = 4
            
            case 0x9D:
                self.SBC("L")
                self.cycle = 4
            
            case 0x9E:
                self.SBC(self.bus.read(self.getreg("HL")))
                self.cycle = 8
            
            case 0x9F:
                self.SBC("A")
                self.cycle = 4
            
            case 0xA0:
                self.AND("B")
                self.cycle = 4
            
            case 0xA1:
                self.AND("C")
                self.cycle = 4
            
            case 0xA2:
                self.AND("D")
                self.cycle = 4
            
            case 0xA3:
                self.AND("E")
                self.cycle = 4
            
            case 0xA4:
                self.AND("H")
                self.cycle = 4
            
            case 0xA5:
                self.AND("L")
                self.cycle = 4
            
            case 0xA6:
                self.AND(self.bus.read(self.getreg("HL")))
                self.cycle = 8
            
            case 0xA7:
                self.AND("A")
                self.cycle = 4
            
            case 0xA8:
                self.XOR("B")
                self.cycle = 4
            
            case 0xA9:
                self.XOR("C")
                self.cycle = 4
            
            case 0xAA:
                self.XOR("D")
                self.cycle = 4
            
            case 0xAB:
                self.XOR("E")
                self.cycle = 4
            
            case 0xAC:
                self.XOR("H")
                self.cycle = 4
            
            case 0xAD:
                self.XOR("L")
                self.cycle = 4
            
            case 0xAE:
                self.XOR(self.bus.read(self.getreg("HL")))
                self.cycle = 8
            
            case 0xAF:
                self.XOR("A")
                self.cycle = 4
            
            case 0xB0:
                self.OR("B")
                self.cycle = 4
            
            case 0xB1:
                self.OR("C")
                self.cycle = 4
            
            case 0xB2:
                self.OR("D")
                self.cycle = 4
            
            case 0xB3:
                self.OR("E")
                self.cycle = 4
            
            case 0xB4:
                self.OR("H")
                self.cycle = 4
            
            case 0xB5:
                self.OR("L")
                self.cycle = 4
            
            case 0xB6:
                self.OR(self.bus.read(self.getreg("HL")))
                self.cycle = 8
            
            case 0xB7:
                self.OR("A")
                self.cycle = 4
            
            case 0xB8:
                self.CP("B")
                self.cycle = 4
            
            case 0xB9:
                self.CP("C")
                self.cycle = 4
            
            case 0xBA:
                self.CP("D")
                self.cycle = 4
            
            case 0xBB:
                self.CP("E")
                self.cycle = 4
            
            case 0xBC:
                self.CP("H")
                self.cycle = 4
            
            case 0xBD:
                self.CP("L")
                self.cycle = 4
            
            case 0xBE:
                self.CP(self.bus.read(self.getreg("HL")))
                self.cycle = 8
            
            case 0xBF:
                self.CP("A")
                self.cycle = 4
            
            case 0xC0:
                self.RET(not self.getreg("z"))
                self.cycle = 8
            
            case 0xC1:
                self.POP("BC")
                self.cycle = 12

            case 0xC2:
                self.JP(not self.getreg("z"))
                self.cycle = 12
            
            case 0xC3:
                self.JP()
                self.cycle = 12
            
            case 0xC4:
                self.CALL(not self.getreg("z"))
                self.cycle = 12

            case 0xC5:
                self.PUSH("BC")
                self.cycle = 16
            
            case 0xC6:
                self.ADD("A", self.getbyteatpc())
                self.cycle = 8
            
            case 0xC7:
                self.RST(0x00)
                self.cycle = 16
            
            case 0xC8:
                self.RET(self.getreg("z"))
                self.cycle = 8
            
            case 0xC9:
                self.RET()
                self.cycle = 16
            
            case 0xCA:
                self.JP(self.getreg("z"))
                self.cycle = 12
            
            case 0xCB:
                self.prefix = 1
                self.cycle = 4

            case 0xCC:
                self.CALL(self.getreg("z"))
                self.cycle = 24
            
            case 0xCD:
                self.CALL()
                self.cycle = 24
            
            case 0xCE:
                self.ADC(self.getbyteatpc())
                self.cycle = 8
            
            case 0xCF:
                self.RST(0x8)
                self.cycle = 16
            
            case 0xD0:
                self.RET(not self.getreg("z"))
                self.cycle = 8
            
            case 0xD1:
                self.POP("DE")
                self.cycle = 12
            
            case 0xD2:
                self.JP(not self.getreg("c"))
                self.cycle = 12
            
            case 0xD3:
                raise ValueError(f"Illegal opcode: {hex(byte)}")
            
            case 0xD4:
                self.CALL(not self.getreg("z"))
                self.cycle = 24

            case 0xD5:
                self.PUSH("DE")
                self.cycle = 16
            
            case 0xD6:
                self.SUB(self.getbyteatpc())
                self.cycle = 8
            
            case 0xD7:
                self.RST(0x10)
                self.cycle = 16
            
            case 0xD8:
                self.RET(self.getreg("c"))
                self.cycle = 8
            
            case 0xD9:
                self.RETI()
                self.cycle = 16
            
            case 0xDA:
                self.JP(self.getreg("c"))
                self.cycle = 12
            
            case 0xDB:
                raise ValueError(f"Illegal opcode: {hex(byte)}")
            
            case 0xDC:
                self.CALL(self.getreg("c"))
                self.cycle = 24
            
            case 0xDD:
                raise ValueError(f"Illegal opcode: {hex(byte)}")
            
            case 0xDE:
                self.SBC(self.getbyteatpc())
                self.cycle = 8
            
            case 0xDF:
                self.RST(0x18)
                self.cycle = 16
            
            case 0xE0:
                self.LDH(True)
                self.cycle = 12
            
            case 0xE1:
                self.POP("HL")
                self.cycle = 12
            
            case 0xE2:
                self.LDC(True)
                self.cycle = 8
            
            case 0xE3:
                raise ValueError(f"Illegal opcode: {hex(byte)}")
            
            case 0xE4:
                raise ValueError(f"Illegal opcode: {hex(byte)}")
            
            case 0xE5:
                self.PUSH("HL")
                self.cycle = 16
            
            case 0xE6:
                self.AND(self.getbyteatpc())
                self.cycle = 8
            
            case 0xE7:
                self.RST(0x20)
                self.cycle = 16
            
            case 0xE8:
                self.ADD("SP", self.getsignedbyteatpc())
                self.cycle = 4

            case 0xE9:
                self.JP(u16 = self.getreg("HL"))
            
            case 0xEA:
                self.LD(self.getwordatpc(), "A")
                self.cycle = 16
            
            case 0xEB:
                raise ValueError(f"Illegal opcode: {hex(byte)}")
            
            case 0xEC:
                raise ValueError(f"Illegal opcode: {hex(byte)}")

            case 0xED:
                raise ValueError(f"Illegal opcode: {hex(byte)}")
            
            case 0xEE:
                self.XOR(self.getbyteatpc())
                self.cycle = 8
            
            case 0xEF:
                self.RST(0x28)
                self.cycle = 16
            
            case 0xF0:
                self.LDH(False)
                self.cycle = 12
            
            case 0xF1:
                self.POP("AF")
                self.cycle = 12
            
            case 0xF2:
                self.LDC(False)
                self.cycle = 8
            
            case 0xF3:
                self.DI()
                self.cycle = 4
            
            case 0xF4:
                raise ValueError(f"Illegal opcode: {hex(byte)}")
            
            case 0xF5:
                self.PUSH("AF")
                self.cycle = 16
            
            case 0xF6:
                self.OR(self.getbyteatpc())
                self.cycle = 8
            
            case 0xF7:
                self.RST(0x30)
                self.cycle = 16
            
            case 0xF8:
                self.LDHL()
                self.cycle = 12
            
            case 0xF9:
                self.LD("SP", "HL")
                self.cycle = 8
            
            case 0xFA:
                self.LD("A", self.bus.read(self.getwordatpc()))
                self.cycle = 16

            case 0xFB:
                self.EI()
                self.cycle = 4
                            
            case 0xFC:
                raise ValueError(f"Illegal opcode: {hex(byte)}")
                            
            case 0xFD:
                raise ValueError(f"Illegal opcode: {hex(byte)}")
            
            case 0xFE:
                self.CP(self.getbyteatpc())
                self.cycle = 8
            
            case 0xFF:
                self.RST(0x38)
                self.cycle = 16
            
    
    def readprefixedopcode(self,byte):

        match(byte):

            case 0x00:
                self.RLC("B")
                self.cycle = 8
            
            case 0x01:
                self.RLC("C")
                self.cycle = 8
            
            case 0x02:
                self.RLC("D")
                self.cycle = 8
            
            case 0x03:
                self.RLC("E")
                self.cycle = 8
            
            case 0x04:
                self.RLC("H")
                self.cycle = 8
            
            case 0x05:
                self.RLC("L")
                self.cycle = 8
            
            case 0x06:
                self.RLC(self.getreg("HL"))
                self.cycle = 16
            
            case 0x07:
                self.RLC("A")
                self.cycle = 8
            
            case 0x08:
                self.RRC("B")
                self.cycle = 8
            
            case 0x09:
                self.RRC("C")
                self.cycle = 8
            
            case 0x0A:
                self.RRC("D")
                self.cycle = 8
            
            case 0x0B:
                self.RRC("E")
                self.cycle = 8
            
            case 0x0C:
                self.RRC("H")
                self.cycle = 8
            
            case 0x0D:
                self.RRC("L")
                self.cycle = 8
            
            case 0x0E:
                self.RRC(self.getreg("HL"))
                self.cycle = 16
            
            case 0x0F:
                self.RRC("A")
                self.cycle = 8
            
            case 0x10:
                self.RL("B")
                self.cycle = 8
            
            case 0x11:
                self.RL("C")
                self.cycle = 8
            
            case 0x12:
                self.RL("D")
                self.cycle = 8
            
            case 0x13:
                self.RL("E")
                self.cycle = 8
            
            case 0x14:
                self.RL("H")
                self.cycle = 8
            
            case 0x15:
                self.RL("L")
                self.cycle = 8
            
            case 0x16:
                self.RL(self.getreg("HL"))
                self.cycle = 16
            
            case 0x17:
                self.RL("A")
                self.cycle = 8
            
            case 0x18:
                self.RR("B")
                self.cycle = 8
            
            case 0x19:
                self.RR("C")
                self.cycle = 8
            
            case 0x1A:
                self.RR("D")
                self.cycle = 8
            
            case 0x1B:
                self.RR("E")
                self.cycle = 8
            
            case 0x1C:
                self.RR("H")
                self.cycle = 8
            
            case 0x1D:
                self.RR("L")
                self.cycle = 8
            
            case 0x1E:
                self.RR(self.getreg("HL"))
                self.cycle = 16
            
            case 0x1F:
                self.RR("A")
                self.cycle = 8
            
            case 0x20:
                self.SLA("B")
                self.cycle = 8
            
            case 0x21:
                self.SLA("C")
                self.cycle = 8
            
            case 0x22:
                self.SLA("D")
                self.cycle = 8
            
            case 0x23:
                self.SLA("E")
                self.cycle = 8
            
            case 0x24:
                self.SLA("H")
                self.cycle = 8
            
            case 0x25:
                self.SLA("L")
                self.cycle = 8
            
            case 0x26:
                self.SLA(self.getreg("HL"))
                self.cycle = 16
            
            case 0x27:
                self.SLA("A")
                self.cycle = 8
            
            case 0x28:
                self.SRA("B")
                self.cycle = 8
            
            case 0x29:
                self.SRA("C")
                self.cycle = 8
            
            case 0x2A:
                self.SRA("D")
                self.cycle = 8
            
            case 0x2B:
                self.SRA("E")
                self.cycle = 8
            
            case 0x2C:
                self.SRA("H")
                self.cycle = 8
            
            case 0x2D:
                self.SRA("L")
                self.cycle = 8
            
            case 0x2E:
                self.SRA(self.getreg("HL"))
                self.cycle = 16
            
            case 0x2F:
                self.SRA("A")
                self.cycle = 8
            
            case 0x30:
                self.SWAP("B")
                self.cycle = 8
            
            case 0x31:
                self.SWAP("C")
                self.cycle = 8
            
            case 0x32:
                self.SWAP("D")
                self.cycle = 8
            
            case 0x33:
                self.SWAP("E")
                self.cycle = 8
            
            case 0x34:
                self.SWAP("H")
                self.cycle = 8
            
            case 0x35:
                self.SWAP("L")
                self.cycle = 8
            
            case 0x36:
                self.SWAP(self.getreg("HL"))
                self.cycle = 16
            
            case 0x37:
                self.SWAP("A")
                self.cycle = 8
            
            case 0x38:
                self.SRL("B")
                self.cycle = 8
            
            case 0x39:
                self.SRL("C")
                self.cycle = 8
            
            case 0x3A:
                self.SRL("D")
                self.cycle = 8
            
            case 0x3B:
                self.SRL("E")
                self.cycle = 8
            
            case 0x3C:
                self.SRL("H")
                self.cycle = 8
            
            case 0x3D:
                self.SRL("L")
                self.cycle = 8
            
            case 0x3E:
                self.SRL(self.getreg("HL"))
                self.cycle = 16
            
            case 0x3F:
                self.SRL("A")
                self.cycle = 8
            
            case 0x40:
                self.BIT(0, "B")
                self.cycle = 8
 
            case 0x41:
                self.BIT(0, "C")
                self.cycle = 8
            
            case 0x42:
                self.BIT(0, "D")
                self.cycle = 8
            
            case 0x43:
                self.BIT(0, "E")
                self.cycle = 8
            
            case 0x44:
                self.BIT(0, "H")
                self.cycle = 8
            
            case 0x45:
                self.BIT(0, "L")
                self.cycle = 8
            
            case 0x46:
                self.BIT(0, self.getreg("HL"))
                self.cycle = 12
            
            case 0x47:
                self.BIT(0, "A")
                self.cycle = 8
            
            case 0x48:
                self.BIT(1, "B")
                self.cycle = 8
            
            case 0x49:
                self.BIT(1, "C")
                self.cycle = 8
            
            case 0x4A:
                self.BIT(1, "D")
                self.cycle = 8
            
            case 0x4B:
                self.BIT(1, "E")
                self.cycle = 8
            
            case 0x4C:
                self.BIT(1, "H")
                self.cycle = 8
            
            case 0x4D:
                self.BIT(1, "L")
                self.cycle = 8
            
            case 0x4E:
                self.BIT(1, self.getreg("HL"))
                self.cycle = 12
            
            case 0x4F:
                self.BIT(1, "A")
                self.cycle = 8
            
            case 0x50:
                self.BIT(2, "B")
                self.cycle = 8
            
            case 0x51:
                self.BIT(2, "C")
                self.cycle = 8
            
            case 0x52:
                self.BIT(2, "D")
                self.cycle = 8
            
            case 0x53:
                self.BIT(2, "E")
                self.cycle = 8
            
            case 0x54:
                self.BIT(2, "H")
                self.cycle = 8
            
            case 0x55:
                self.BIT(2, "L")
                self.cycle = 8
            
            case 0x56:
                self.BIT(2, self.getreg("HL"))
                self.cycle = 12
            
            case 0x57:
                self.BIT(2, "A")
                self.cycle = 8
            
            case 0x58:
                self.BIT(3, "B")
                self.cycle = 8
            
            case 0x59:
                self.BIT(3, "C")
                self.cycle = 8
            
            case 0x5A:
                self.BIT(3, "D")
                self.cycle = 8
            
            case 0x5B:
                self.BIT(3, "E")
                self.cycle = 8
            
            case 0x5C:
                self.BIT(3, "H")
                self.cycle = 8
            
            case 0x5D:
                self.BIT(3, "L")
                self.cycle = 8
            
            case 0x5E:
                self.BIT(3, self.getreg("HL"))
                self.cycle = 12
            
            case 0x5F:
                self.BIT(3, "A")
                self.cycle = 8
            
            case 0x60:
                self.BIT(4, "B")
                self.cycle = 8
            
            case 0x61:
                self.BIT(4, "C")
                self.cycle = 8
            
            case 0x62:
                self.BIT(4, "D")
                self.cycle = 8
            
            case 0x63:
                self.BIT(4, "E")
                self.cycle = 8
            
            case 0x64:
                self.BIT(4, "H")
                self.cycle = 8
            
            case 0x65:
                self.BIT(4, "L")
                self.cycle = 8
            
            case 0x66:
                self.BIT(4, self.getreg("HL"))
                self.cycle = 12
            
            case 0x67:
                self.BIT(4, "A")
                self.cycle = 8
            
            case 0x68:
                self.BIT(5, "B")
                self.cycle = 8
            
            case 0x69:
                self.BIT(5, "C")
                self.cycle = 8
            
            case 0x6A:
                self.BIT(5, "D")
                self.cycle = 8
            
            case 0x6B:
                self.BIT(5, "E")
                self.cycle = 8
            
            case 0x6C:
                self.BIT(5, "H")
                self.cycle = 8
            
            case 0x6D:
                self.BIT(5, "L")
                self.cycle = 8
            
            case 0x6E:
                self.BIT(5, self.getreg("HL"))
                self.cycle = 12
            
            case 0x6F:
                self.BIT(5, "A")
                self.cycle = 8
            
            case 0x70:
                self.BIT(6, "B")
                self.cycle = 8
            
            case 0x71:
                self.BIT(6, "C")
                self.cycle = 8
            
            case 0x72:
                self.BIT(6, "D")
                self.cycle = 8
            
            case 0x73:
                self.BIT(6, "E")
                self.cycle = 8
            
            case 0x74:
                self.BIT(6, "H")
                self.cycle = 8
            
            case 0x75:
                self.BIT(6, "L")
                self.cycle = 8
            
            case 0x76:
                self.BIT(6, self.getreg("HL"))
                self.cycle = 12
            
            case 0x77:
                self.BIT(6, "A")
                self.cycle = 8
            
            case 0x78:
                self.BIT(7, "B")
                self.cycle = 8
            
            case 0x79:
                self.BIT(7, "C")
                self.cycle = 8
            
            case 0x7A:
                self.BIT(7, "D")
                self.cycle = 8
            
            case 0x7B:
                self.BIT(7, "E")
                self.cycle = 8
            
            case 0x7C:
                self.BIT(7, "H")
                self.cycle = 8
            
            case 0x7D:
                self.BIT(7, "L")
                self.cycle = 8
            
            case 0x7E:
                self.BIT(7, self.getreg("HL"))
                self.cycle = 12
            
            case 0x7F:
                self.BIT(7, "A")
                self.cycle = 8
            
            case 0x80:
                self.RES(0, "B")
                self.cycle = 8
            
            case 0x81:
                self.RES(0, "C")
                self.cycle = 8
            
            case 0x82:
                self.RES(0, "D")
                self.cycle = 8
            
            case 0x83:
                self.RES(0, "E")
                self.cycle = 8
            
            case 0x84:
                self.RES(0, "H")
                self.cycle = 8
            
            case 0x85:
                self.RES(0, "L")
                self.cycle = 8
            
            case 0x86:
                self.RES(0, self.getreg("HL"))
                self.cycle = 12
            
            case 0x87:
                self.RES(0, "A")
                self.cycle = 8
            
            case 0x88:
                self.RES(1, "B")
                self.cycle = 8
            
            case 0x89:
                self.RES(1, "C")
                self.cycle = 8
            
            case 0x8A:
                self.RES(1, "D")
                self.cycle = 8
            
            case 0x8B:
                self.RES(1, "E")
                self.cycle = 8
            
            case 0x8C:
                self.RES(1, "H")
                self.cycle = 8
            
            case 0x8D:
                self.RES(1, "L")
                self.cycle = 8
            
            case 0x8E:
                self.RES(1, self.getreg("HL"))
                self.cycle = 12
            
            case 0x8F:
                self.RES(1, "A")
                self.cycle = 8
            
            case 0x90:
                self.RES(2, "B")
                self.cycle = 8
            
            case 0x91:
                self.RES(2, "C")
                self.cycle = 8
            
            case 0x92:
                self.RES(2, "D")
                self.cycle = 8
            
            case 0x93:
                self.RES(2, "E")
                self.cycle = 8
            
            case 0x94:
                self.RES(2, "H")
                self.cycle = 8
            
            case 0x95:
                self.RES(2, "L")
                self.cycle = 8
            
            case 0x96:
                self.RES(2, self.getreg("HL"))
                self.cycle = 12
            
            case 0x97:
                self.RES(2, "A")
                self.cycle = 8
            
            case 0x98:
                self.RES(3, "B")
                self.cycle = 8
            
            case 0x99:
                self.RES(3, "C")
                self.cycle = 8
            
            case 0x9A:
                self.RES(3, "D")
                self.cycle = 8
            
            case 0x9B:
                self.RES(3, "E")
                self.cycle = 8
            
            case 0x9C:
                self.RES(3, "H")
                self.cycle = 8
            
            case 0x9D:
                self.RES(3, "L")
                self.cycle = 8
            
            case 0x9E:
                self.RES(3, self.getreg("HL"))
                self.cycle = 12
            
            case 0x9F:
                self.RES(3, "A")
                self.cycle = 8
            
            case 0xA0:
                self.RES(4, "B")
                self.cycle = 8
            
            case 0xA1:
                self.RES(4, "C")
                self.cycle = 8
            
            case 0xA2:
                self.RES(4, "D")
                self.cycle = 8
            
            case 0xA3:
                self.RES(4, "E")
                self.cycle = 8
            
            case 0xA4:
                self.RES(4, "H")
                self.cycle = 8
            
            case 0xA5:
                self.RES(4, "L")
                self.cycle = 8
            
            case 0xA6:
                self.RES(4, self.getreg("HL"))
                self.cycle = 12
            
            case 0xA7:
                self.RES(4, "A")
                self.cycle = 8
            
            case 0xA8:
                self.RES(5, "B")
                self.cycle = 8
            
            case 0xA9:
                self.RES(5, "C")
                self.cycle = 8
            
            case 0xAA:
                self.RES(5, "D")
                self.cycle = 8
            
            case 0xAB:
                self.RES(5, "E")
                self.cycle = 8
            
            case 0xAC:
                self.RES(5, "H")
                self.cycle = 8
            
            case 0xAD:
                self.RES(5, "L")
                self.cycle = 8
            
            case 0xAE:
                self.RES(5, self.getreg("HL"))
                self.cycle = 12
            
            case 0xAF:
                self.RES(5, "A")
                self.cycle = 8
            
            case 0xB0:
                self.RES(6, "B")
                self.cycle = 8
            
            case 0xB1:
                self.RES(6, "C")
                self.cycle = 8
            
            case 0xB2:
                self.RES(6, "D")
                self.cycle = 8
            
            case 0xB3:
                self.RES(6, "E")
                self.cycle = 8
            
            case 0xB4:
                self.RES(6, "H")
                self.cycle = 8
            
            case 0xB5:
                self.RES(6, "L")
                self.cycle = 8
            
            case 0xB6:
                self.RES(6, self.getreg("HL"))
                self.cycle = 12
            
            case 0xB7:
                self.RES(6, "A")
                self.cycle = 8
            
            case 0xB8:
                self.RES(7, "B")
                self.cycle = 8
            
            case 0xB9:
                self.RES(7, "C")
                self.cycle = 8
            
            case 0xBA:
                self.RES(7, "D")
                self.cycle = 8
            
            case 0xBB:
                self.RES(7, "E")
                self.cycle = 8
            
            case 0xBC:
                self.RES(7, "H")
                self.cycle = 8
            
            case 0xBD:
                self.RES(7, "L")
                self.cycle = 8
            
            case 0xBE:
                self.RES(7, self.getreg("HL"))
                self.cycle = 12
            
            case 0xBF:
                self.RES(7, "A")
                self.cycle = 8
            
            case 0xC0:
                self.SET(0, "B")
                self.cycle = 8
            
            case 0xC1:
                self.SET(0, "C")
                self.cycle = 8
            
            case 0xC2:
                self.SET(0, "D")
                self.cycle = 8
            
            case 0xC3:
                self.SET(0, "E")
                self.cycle = 8
            
            case 0xC4:
                self.SET(0, "H")
                self.cycle = 8
            
            case 0xC5:
                self.SET(0, "L")
                self.cycle = 8
            
            case 0xC6:
                self.SET(0, self.getreg("HL"))
                self.cycle = 12
            
            case 0xC7:
                self.SET(0, "A")
                self.cycle = 8
            
            case 0xC8:
                self.SET(1, "B")
                self.cycle = 8
            
            case 0xC9:
                self.SET(1, "C")
                self.cycle = 8
            
            case 0xCA:
                self.SET(1, "D")
                self.cycle = 8
            
            case 0xCB:
                self.SET(1, "E")
                self.cycle = 8
            
            case 0xCC:
                self.SET(1, "H")
                self.cycle = 8
            
            case 0xCD:
                self.SET(1, "L")
                self.cycle = 8
            
            case 0xCE:
                self.SET(1, self.getreg("HL"))
                self.cycle = 12
            
            case 0xCF:
                self.SET(1, "A")
                self.cycle = 8
            
            case 0xD0:
                self.SET(2, "B")
                self.cycle = 8
            
            case 0xD1:
                self.SET(2, "C")
                self.cycle = 8
            
            case 0xD2:
                self.SET(2, "D")
                self.cycle = 8
            
            case 0xD3:
                self.SET(2, "E")
                self.cycle = 8
            
            case 0xD4:
                self.SET(2, "H")
                self.cycle = 8
            
            case 0xD5:
                self.SET(2, "L")
                self.cycle = 8
            
            case 0xD6:
                self.SET(2, self.getreg("HL"))
                self.cycle = 12
            
            case 0xD7:
                self.SET(2, "A")
                self.cycle = 8
            
            case 0xD8:
                self.SET(3, "B")
                self.cycle = 8
            
            case 0xD9:
                self.SET(3, "C")
                self.cycle = 8
            
            case 0xDA:
                self.SET(3, "D")
                self.cycle = 8
            
            case 0xDB:
                self.SET(3, "E")
                self.cycle = 8
            
            case 0xDC:
                self.SET(3, "H")
                self.cycle = 8
            
            case 0xDD:
                self.SET(3, "L")
                self.cycle = 8
            
            case 0xDE:
                self.SET(3, self.getreg("HL"))
                self.cycle = 12
            
            case 0xDF:
                self.SET(3, "A")
                self.cycle = 8
            
            case 0xE0:
                self.SET(4, "B")
                self.cycle = 8
            
            case 0xE1:
                self.SET(4, "C")
                self.cycle = 8
            
            case 0xE2:
                self.SET(4, "D")
                self.cycle = 8
            
            case 0xE3:
                self.SET(4, "E")
                self.cycle = 8
            
            case 0xE4:
                self.SET(4, "H")
                self.cycle = 8
            
            case 0xE5:
                self.SET(4, "L")
                self.cycle = 8
            
            case 0xE6:
                self.SET(4, self.getreg("HL"))
                self.cycle = 12
            
            case 0xE7:
                self.SET(4, "A")
                self.cycle = 8
            
            case 0xE8:
                self.SET(5, "B")
                self.cycle = 8
            
            case 0xE9:
                self.SET(5, "C")
                self.cycle = 8
            
            case 0xEA:
                self.SET(5, "D")
                self.cycle = 8
            
            case 0xEB:
                self.SET(5, "E")
                self.cycle = 8
            
            case 0xEC:
                self.SET(5, "H")
                self.cycle = 8
            
            case 0xED:
                self.SET(5, "L")
                self.cycle = 8
            
            case 0xEE:
                self.SET(5, self.getreg("HL"))
                self.cycle = 12
            
            case 0xEF:
                self.SET(5, "A")
                self.cycle = 8
            
            case 0xF0:
                self.SET(6, "B")
                self.cycle = 8
            
            case 0xF1:
                self.SET(6, "C")
                self.cycle = 8
            
            case 0xF2:
                self.SET(6, "D")
                self.cycle = 8
            
            case 0xF3:
                self.SET(6, "E")
                self.cycle = 8
            
            case 0xF4:
                self.SET(6, "H")
                self.cycle = 8
            
            case 0xF5:
                self.SET(6, "L")
                self.cycle = 8
            
            case 0xF6:
                self.SET(6, self.getreg("HL"))
                self.cycle = 12
            
            case 0xF7:
                self.SET(6, "A")
                self.cycle = 8
            
            case 0xF8:
                self.SET(7, "B")
                self.cycle = 8
            
            case 0xF9:
                self.SET(7, "C")
                self.cycle = 8
            
            case 0xFA:
                self.SET(7, "D")
                self.cycle = 8
            
            case 0xFB:
                self.SET(7, "E")
                self.cycle = 8
            
            case 0xFC:
                self.SET(7, "H")
                self.cycle = 8
            
            case 0xFD:
                self.SET(7, "L")
                self.cycle = 8
            
            case 0xFE:
                self.SET(7, self.getreg("HL"))
                self.cycle = 12
            
            case 0xFF:
                self.SET(7, "A")
                self.cycle = 8
            