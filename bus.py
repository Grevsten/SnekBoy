import cart
import cpu

class Bus():
    
    def __init__(self, ram = [None]*0xFFFF):
        self.ram = ram
    
    def write(self, addr, data):
        if (addr < 0x8000):
            self.ram[addr] = data

    def read(self, addr) -> int:
        if (addr < 0x8000):
            return self.ram[addr]

test = Bus()

testcart = Cart.Cartridge()
