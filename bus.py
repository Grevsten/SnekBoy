import cart
import cpu


class Bus():
    
    def __init__(self, ram = [0x0]*0x10000):
        self.ram = ram
    
    def write(self, addr, data):
        "Writes to address in RAM."
        if addr <= 0xFFFF:
            self.ram[addr] = data

    def read(self, addr) -> int:
        "Returns value at address in RAM."
        if addr <= 0xFFFF:
            return self.ram[addr]
        else:
            raise ValueError(f"Adress out of range.")

testbus = Bus()

testcart = cart.Cartridge(open('ROMS/example.gb', "rb"))

testcpu = cpu.LR35902(testbus)