variable "resource_group_name" {
  description = "The name of the Azure resource group."
  type        = string
  default     = "microedge-resource-group"
}

variable "location" {
  description = "The Azure region."
  type        = string
  default     = "westeurope"
}

variable "vm_size" {
  description = "The size of the Azure VM."
  type        = string
  default     = "Standard_D2s_v3"
}

variable "admin_username" {
  description = "The admin username for the VM."
  type        = string
  default     = "azureadmin"
}

variable "ssh_public_key" {
  description = "The SSH public key to be added to the VM."
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "vnet_name" {
  description = "The name of the virtual network."
  type        = string
  default     = "microedge-vnet"
}

variable "subnet_name" {
  description = "The name of the subnet."
  type        = string
  default     = "microedge-subnet"
}

variable "public_ip_name" {
  description = "The name of the public IP."
  type        = string
  default     = "microedge-public-ip"
}

variable "nsg_name" {
  description = "The name of the network security group."
  type        = string
  default     = "microedge-nsg"
}

variable "nic_name" {
  description = "The name of the network interface."
  type        = string
  default     = "microedge-nic"
}

variable "vm_name" {
  description = "The name of the virtual machine."
  type        = string
  default     = "microedge-vm"
}