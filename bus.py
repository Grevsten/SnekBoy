import cart
import cpu

class Bus():
    
    def __init__(self, ram = [0x0]*0xFFFF):
        self.ram = ram
    
    def write(self, addr, data):
        "Writes to address in RAM."
        if addr <= 0xFFFF:
            self.ram[addr] = data

    def read(self, addr) -> int:
        "Returns value at address in RAM."
        if addr <= 0xFFFF:
            return self.ram[addr]

testbus = Bus()

testcart = cart.Cartridge()

testcpu = cpu.LR35902(testbus)
