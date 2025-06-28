# Using IronShell with a Custom Domain

This guide will help you set up IronShell to run behind your own domain, with nginx as a reverse proxy. It covers two ways to run the Python server (systemd and PufferPanel), and provides a ready-to-use nginx config. At the end, you'll see how to secure your site with HTTPS using certbot.

## 1. Running the Python Server

### Option A: systemd

1. **Create a systemd service file:**

   ```ini
   [Unit]
   Description=IronShell Flask-Waitress Server
   After=network.target

   [Service]
   User=youruser
   WorkingDirectory=/path/to/your/project
   ExecStart=/usr/bin/python3 server.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

2. **Save as** `/etc/systemd/system/ironshell.service` (or similar).
3. **Enable and start the service:**

   ```sh
   sudo systemctl daemon-reload
   sudo systemctl enable ironshell
   sudo systemctl start ironshell
   ```

4. **Check status:**

   ```sh
   sudo systemctl status ironshell
   ```

---

### Option B: PufferPanel

> I'd like to say PufferPanel 2.7.1 works best for me.

1. Import your project into PufferPanel as a `discord.py Bot` template or create custom one.
2. Set the startup file to:

   ```sh
   server.py
   ```

3. Install the server via `INSTALL` button.
4. Start the server from the PufferPanel UI.

> For any missing packages and simillar errors - follow `discord.py Bot` template guide on resolving them.

## 2. Nginx Reverse Proxy Config

This config will forward all requests from your domain to the IronShell server running on `127.0.0.1:7869`.

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass         http://127.0.0.1:7869;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
    }
}
```

- Replace `yourdomain.com` with your actual domain.
- Reload nginx after saving:

  ```sh
  sudo systemctl reload nginx
  ```

## 3. Enable HTTPS with Certbot

1. Install certbot and the nginx plugin:

   ```sh
   sudo apt install certbot python3-certbot-nginx
   ```

2. Run certbot:

   ```sh
   sudo certbot --nginx -d yourdomain.com
   ```

3. Follow the prompts to enable HTTPS.

## 4. Test Your Setup

- Visit `https://yourdomain.com/install/app` in your browser or run:

  ```powershell
  iwr https://yourdomain.com/install/app | iex
  ```

- You should see the PowerShell installer script or the app install process.

**That's it!** Your IronShell server is now running behind your domain, with nginx handling HTTPS and proxying requests to your Python server.
