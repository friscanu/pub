terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.116.0"
    }
  }
}

provider "azurerm" {
  features {}
  skip_provider_registration = true
}

# Data source to reference the existing resource group
data "azurerm_resource_group" "default" {
  name = var.resource_group_name
}

# Data source to reference the existing virtual network
data "azurerm_virtual_network" "default" {
  name                = var.vnet_name
  resource_group_name = data.azurerm_resource_group.default.name
}

# Data source to reference the existing subnet
data "azurerm_subnet" "default" {
  name                 = var.subnet_name
  resource_group_name  = data.azurerm_resource_group.default.name
  virtual_network_name = data.azurerm_virtual_network.default.name
}

resource "azurerm_network_security_group" "default" {
  name                = var.nsg_name
  location            = data.azurerm_resource_group.default.location
  resource_group_name = data.azurerm_resource_group.default.name

  security_rule {
    name                       = "SSH"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

resource "azurerm_network_interface" "default" {
  name                = var.nic_name
  location            = data.azurerm_resource_group.default.location
  resource_group_name = data.azurerm_resource_group.default.name

  ip_configuration {
    name                          = "microedge-ipconfig"
    subnet_id                     = data.azurerm_subnet.default.id
    private_ip_address_allocation = "Dynamic"
  }
}

resource "azurerm_network_interface_security_group_association" "default" {
  network_interface_id      = azurerm_network_interface.default.id
  network_security_group_id = azurerm_network_security_group.default.id
}

resource "azurerm_linux_virtual_machine" "default" {
  name                  = var.vm_name
  resource_group_name   = data.azurerm_resource_group.default.name
  location              = data.azurerm_resource_group.default.location
  size                  = var.vm_size
  admin_username        = var.admin_username
  network_interface_ids = [azurerm_network_interface.default.id]

  admin_ssh_key {
    username   = var.admin_username
    public_key = file(var.ssh_public_key)
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Debian"
    offer     = "debian-12"
    sku       = "12-gen2"
    version   = "latest"
  }
}

output "private_ip_address" {
  description = "The private IP address of the VM"
  value       = azurerm_network_interface.default.private_ip_address
}