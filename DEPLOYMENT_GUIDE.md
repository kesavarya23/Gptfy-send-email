# 🚀 Deployment Guide - Vercel + Railway

Deploy your Salesforce Email Sender with a beautiful UI to the cloud!

## 📋 Overview

- **Frontend + Backend:** Vercel (Full-stack deployment)
- **Alternative Backend:** Railway (If you want separate backend)
- **Database:** Not needed (stateless application)

---

## 🎯 Option 1: Vercel (Full-Stack) - RECOMMENDED

Deploy everything to Vercel - simplest option!

### Step 1: Prepare Repository

Your code is already on GitHub:
```
https://github.com/kesavarya23/Gptfy-send-email
```

Make sure these files exist (they do!):
- ✅ `vercel.json` - Vercel configuration
- ✅ `requirements.txt` - Python dependencies
- ✅ `runtime.txt` - Python version
- ✅ `app.py` - Flask application

### Step 2: Deploy to Vercel

1. **Go to Vercel:**
   - Visit: https://vercel.com
   - Sign up/Login with GitHub

2. **Import Project:**
   - Click "New Project"
   - Import `kesavarya23/Gptfy-send-email`
   - Click "Import"

3. **Configure:**
   - Framework Preset: **Other**
   - Build Command: (leave empty)
   - Output Directory: (leave empty)
   - Install Command: `pip install -r requirements.txt`

4. **Deploy:**
   - Click "Deploy"
   - Wait 2-3 minutes
   - Get your URL: `https://your-project.vercel.app`

### Step 3: Test It!

Open your Vercel URL in browser:
```
https://gptfy-send-email.vercel.app
```

🎉 **Done! Your app is live!**

---

## 🎯 Option 2: Railway (Backend) + Vercel (Frontend)

If you want separate frontend and backend:

### Railway Backend Setup:

1. **Go to Railway:**
   - Visit: https://railway.app
   - Sign up/Login with GitHub

2. **New Project:**
   - Click "New Project"
   - Choose "Deploy from GitHub repo"
   - Select `Gptfy-send-email`

3. **Configure:**
   - Railway auto-detects Python
   - No configuration needed!

4. **Get URL:**
   - Railway gives you: `https://your-app.railway.app`
   - Copy this URL

### Vercel Frontend Setup:

1. Deploy to Vercel (same as Option 1)

2. **Update API URL:**
   - In `templates/index.html`, update fetch URL:
   ```javascript
   const response = await fetch('https://your-app.railway.app/send_emails', {
   ```

3. **Redeploy** to Vercel

---

## 📝 Simple Step-by-Step (Vercel Only)

### For Complete Beginners:

**Step 1:** Push latest code to GitHub
```bash
cd "c:\Projects\Gptfy send email\Gptfy-send-email"
git add .
git commit -m "Add deployment files"
git push origin main
```

**Step 2:** Go to Vercel
- Open: https://vercel.com
- Click "Sign Up" (use GitHub)

**Step 3:** Import Your Repository
- Click "Add New..." → "Project"
- Find "Gptfy-send-email"
- Click "Import"

**Step 4:** Deploy
- Click "Deploy" (don't change any settings)
- Wait 2-3 minutes
- Click the URL Vercel gives you

**Step 5:** Done!
- Share your URL with anyone
- They can use it from anywhere in the world!

---

## 🌐 Your Deployed App Will Have:

✅ **Public URL:** `https://your-project.vercel.app`
✅ **HTTPS:** Secure by default
✅ **Fast:** Global CDN
✅ **Free:** No cost for small projects
✅ **Auto-deploy:** Updates when you push to GitHub

---

## 🔧 Configuration Files Explained

### `vercel.json`
```json
{
  "builds": [
    { "src": "app.py", "use": "@vercel/python" }
  ],
  "routes": [
    { "src": "/(.*)", "dest": "app.py" }
  ]
}
```
Tells Vercel this is a Python app.

### `runtime.txt`
```
python-3.11.0
```
Specifies Python version.

### `Procfile` (for Railway)
```
web: gunicorn app:app
```
Tells Railway how to run the app.

---

## 🎨 Custom Domain (Optional)

### Add Your Own Domain:

1. **In Vercel:**
   - Go to Project Settings
   - Click "Domains"
   - Add your domain (e.g., `emails.yourdomain.com`)

2. **Update DNS:**
   - Add CNAME record in your domain provider
   - Point to Vercel

3. **Wait:**
   - SSL certificate auto-generated
   - Domain ready in 5-10 minutes

---

## 📊 Monitoring

### Vercel Dashboard:
- View deployments
- Check logs
- Monitor usage
- See analytics

### Railway Dashboard:
- View metrics
- Check logs
- Monitor resources

---

## 🐛 Troubleshooting

### Deployment Failed:

**Check:**
1. `requirements.txt` is correct
2. All files are committed to GitHub
3. No syntax errors in Python code

**Fix:**
```bash
# Test locally first
python app.py
# If it works locally, it will work on Vercel
```

### 500 Internal Server Error:

**Check Vercel Logs:**
1. Go to Vercel Dashboard
2. Click your project
3. Click "Deployments"
4. Click latest deployment
5. Click "View Function Logs"

**Common Issues:**
- Missing dependencies → Add to `requirements.txt`
- Import errors → Check file paths
- Environment variables → Add in Vercel settings

### CORS Errors:

Already fixed! `flask-cors` is installed and enabled.

---

## 💰 Cost

### Free Tier Limits:

**Vercel:**
- ✅ 100GB bandwidth/month
- ✅ Unlimited deployments
- ✅ Unlimited requests
- ✅ Custom domains
- ✅ HTTPS included

**Railway:**
- ✅ $5 free credit/month
- ✅ ~500 hours runtime
- ✅ Enough for most use cases

**Perfect for:**
- Personal projects
- Testing
- Small teams
- Side projects

---

## 🚀 Quick Deploy Commands

### Push to GitHub:
```bash
cd "c:\Projects\Gptfy send email\Gptfy-send-email"
git add .
git commit -m "Ready for deployment"
git push origin main
```

### Vercel CLI (Optional):
```bash
npm install -g vercel
cd "c:\Projects\Gptfy send email\Gptfy-send-email"
vercel
```

### Railway CLI (Optional):
```bash
npm install -g railway
cd "c:\Projects\Gptfy send email\Gptfy-send-email"
railway login
railway up
```

---

## 📱 Share Your Deployed App

Once deployed, share this with anyone:

```
🌐 Salesforce Email Sender

Try it here: https://your-project.vercel.app

Features:
✅ Generate random Salesforce emails
✅ Send to any recipient
✅ Beautiful web interface
✅ No installation needed
✅ Works on mobile/desktop

Just open the link and use it!
```

---

## ✅ Deployment Checklist

Before deploying:
- [ ] Code pushed to GitHub
- [ ] `vercel.json` exists
- [ ] `requirements.txt` updated
- [ ] `runtime.txt` exists
- [ ] Tested locally (`python app.py`)
- [ ] CORS enabled in `app.py`

Ready to deploy:
- [ ] Vercel account created
- [ ] Repository imported
- [ ] Deployment successful
- [ ] URL works
- [ ] Tested sending emails

Share:
- [ ] URL shared with team
- [ ] Documentation updated
- [ ] Custom domain added (optional)

---

## 🎉 Summary

**Easiest Way:**
1. Push code to GitHub ✅ (Already done!)
2. Go to Vercel.com
3. Import your repository
4. Click "Deploy"
5. Get your URL
6. Share with the world! 🌍

**Your app will be live at:**
```
https://gptfy-send-email.vercel.app
(or your custom domain)
```

**Anyone can use it:**
- No installation
- Just open URL
- Fill form
- Send emails!

---

**Ready to deploy? Let's do it!** 🚀
