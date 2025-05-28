# Localhost Configuration Guide

This guide explains how to set up the n0name Trading Dashboard to use standard localhost URLs instead of custom domain routing.

## Overview

The web UI has been updated to use:
- **Frontend**: `https://localhost:5173` (Vite dev server with HTTPS)
- **Backend API**: `https://localhost:8000` (FastAPI with HTTPS)
- **No hosts file modification required**

## Quick Setup

### 1. Generate SSL Certificates

Run the certificate generation script:

```bash
python utils/web_ui/generate_certificates.py
```

This creates self-signed certificates for local HTTPS development.

### 2. Start the Application

```bash
python n0name.py
```

The application will:
- Start the backend API on `https://localhost:8000`
- Start the frontend dev server on `https://localhost:5173`
- Automatically open your browser to the dashboard

### 3. Accept Certificate Warning

Since we use self-signed certificates for local development, your browser will show a security warning. This is normal and safe for local development.

**To proceed:**
1. Click "Advanced" or "Show details"
2. Click "Proceed to localhost" or "Accept risk"

## Configuration Details

### Frontend Configuration

- **Vite Config**: `utils/web_ui/project/vite.config.ts`
  - Uses `localhost:5173` with HTTPS
  - Proxies API requests to `https://localhost:8000`
  
- **API Configuration**: `utils/web_ui/project/src/config/api.ts`
  - Centralized API URL management
  - Environment variable support

### Backend Configuration

- **CORS Settings**: Updated to allow localhost origins
- **HTTPS Support**: Uses generated SSL certificates
- **Fallback**: Falls back to HTTP if certificates unavailable

### Environment Variables

Create `.env.local` in the project directory for custom configuration:

```env
VITE_API_BASE_URL=https://localhost:8000/api
VITE_APP_TITLE=n0name Trading Dashboard
```

## Migration from Custom Domain

If you're migrating from the previous custom domain setup:

### Manual Migration Steps

1. **Remove hosts file entry**: Remove `127.0.0.1 n0name` from your hosts file
2. **Update bookmarks**: Change bookmarks from `http://n0name` to `https://localhost:5173`
3. **Clear browser cache**: Clear cache for the old domain

## Troubleshooting

### Certificate Issues

**Problem**: Browser shows "NET::ERR_CERT_AUTHORITY_INVALID"
**Solution**: This is expected for self-signed certificates. Click "Advanced" → "Proceed to localhost"

**Problem**: Certificate generation fails
**Solution**: 
- Install OpenSSL
- Windows: Download from [Win32OpenSSL](https://slproweb.com/products/Win32OpenSSL.html)
- macOS: `brew install openssl`
- Linux: `sudo apt-get install openssl`

### Connection Issues

**Problem**: Cannot connect to API
**Solution**: 
- Ensure backend is running on port 8000
- Check firewall settings
- Verify certificates are generated

**Problem**: Frontend won't start
**Solution**:
- Check if port 5173 is available
- Run `npm install` in the project directory
- Check Node.js version (requires Node 16+)

### Port Conflicts

If ports 5173 or 8000 are in use:

1. **Change frontend port**: Edit `vite.config.ts` and update the port
2. **Change backend port**: Edit the uvicorn configuration in `api/main.py`
3. **Update environment variables**: Update `VITE_API_BASE_URL` accordingly

## Security Notes

### Development vs Production

- **Development**: Uses self-signed certificates (this setup)
- **Production**: Should use proper SSL certificates from a CA

### Self-Signed Certificate Security

- ✅ **Safe for local development**
- ✅ **Encrypts traffic between browser and server**
- ⚠️ **Not suitable for production**
- ⚠️ **Browser warnings are normal**

## Advanced Configuration

### Custom Certificate

To use your own certificates:

1. Place your certificate files in `utils/web_ui/project/certs/`
2. Name them `localhost-cert.pem` and `localhost-key.pem`
3. Restart the application

### Different Ports

To use different ports:

1. Update `vite.config.ts` for frontend port
2. Update `api/main.py` for backend port
3. Update `.env.local` with new API URL

### HTTP Fallback

To disable HTTPS and use HTTP only:

1. Remove or rename the certificates directory
2. Update `.env.local`: `VITE_API_BASE_URL=http://localhost:8000/api`
3. The application will automatically fall back to HTTP

## Benefits of Localhost Configuration

1. **No admin privileges required**: No hosts file modification
2. **Standard development setup**: Uses conventional localhost URLs
3. **HTTPS support**: Secure local development
4. **Better browser compatibility**: No custom domain issues
5. **Easier deployment**: Standard configuration patterns
6. **Development best practices**: Follows modern web development standards

## Support

If you encounter issues with the localhost configuration:

1. Check the troubleshooting section above
2. Verify your system meets the requirements
3. Review the console logs for error messages
4. Ensure all dependencies are installed correctly 