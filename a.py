import torch
torch.cuda.is_available()
print(torch.cuda.get_device_name(0))