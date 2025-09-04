# Documents Folder

This folder contains important setup guides that are automatically attached to VPN account creation emails.

## Files:

### TeBS-FortiToken 2FA Guide.V1.0.pdf
Guide for setting up two-factor authentication using FortiToken for VPN access.

### TeBS-VPN Client Setup Guide.V4.0.pdf
Comprehensive guide for configuring VPN client software on various operating systems.

## Usage:
These documents are automatically attached to VPN account creation emails by the automation service. The files are referenced in `automation_service.py` in the `open_outlook_and_draft_email()` method.

## File Organization:
- Location: `app/static/documents/`
- Purpose: Email attachments for VPN setup
- Access: Served via Flask static files when needed
