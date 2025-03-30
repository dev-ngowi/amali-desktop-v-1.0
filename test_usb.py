import usb.core
import usb.util

# Find the device
dev = usb.core.find(idVendor=0x1d90, idProduct=0x2060)
if dev is None:
    print("Printer not found!")
    exit()

# Set configuration (usually 0 or 1)
dev.set_configuration()

# Print device details
print("Device:", dev)

# Iterate through configurations and interfaces
for cfg in dev:
    print(f"Configuration {cfg.bConfigurationValue}:")
    for intf in cfg:
        print(f"  Interface {intf.bInterfaceNumber}:")
        for ep in intf:
            print(f"    Endpoint Address: {hex(ep.bEndpointAddress)}, Type: {usb.util.endpoint_type(ep.bmAttributes)}")
            
            
            
            
            
            
            
            