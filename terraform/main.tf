terraform {
  required_version = ">= 1.5"
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 4.0" }
    google  = { source = "hashicorp/google", version = "~> 6.0" }
  }
}

variable "resource_group" { type = string }
variable "location" { type = string }
variable "gcp_project" { type = string }

# One registry per cloud, with admin access off so pulls go through identities.
resource "azurerm_container_registry" "acr" {
  name                = "supplychainacr"
  resource_group_name = var.resource_group
  location            = var.location
  sku                 = "Premium"
  admin_enabled       = false
}

resource "google_artifact_registry_repository" "images" {
  project       = var.gcp_project
  location      = "us"
  repository_id = "images"
  format        = "DOCKER"

  cleanup_policies {
    id     = "keep-recent"
    action = "KEEP"
    most_recent_versions { keep_count = 20 }
  }
}
