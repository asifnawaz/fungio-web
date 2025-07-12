import { NextApiRequest, NextApiResponse } from 'next';
import fs from 'fs';
import path from 'path';
import { Resend } from 'resend';

interface BetaSignupData {
  email: string;
  timestamp: string;
}

// Initialize Resend
const resend = new Resend(process.env.RESEND_API_KEY);

// Send welcome email to beta tester
async function sendWelcomeEmail(email: string, position: number) {
  if (!process.env.RESEND_API_KEY) {
    console.warn('RESEND_API_KEY not found, skipping email send');
    return;
  }

  try {
    const { data, error } = await resend.emails.send({
      from: 'Fungio <noreply@fungio.network>',
      to: [email],
      subject: '🍄 Welcome to the Fungio Beta - Your Spore Has Been Planted',
      html: createWelcomeEmailHTML(position),
    });

    if (error) {
      console.error('Failed to send welcome email:', error);
    } else {
      console.log('Welcome email sent successfully:', data);
    }
  } catch (error) {
    console.error('Error sending welcome email:', error);
  }
}

// Create fungal-themed welcome email HTML
function createWelcomeEmailHTML(position: number): string {
  return `
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Welcome to Fungio Beta</title>
      <style>
        body {
          margin: 0;
          padding: 0;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
          color: #ffffff;
          line-height: 1.6;
        }
        .container {
          max-width: 600px;
          margin: 0 auto;
          padding: 40px 20px;
        }
        .header {
          text-align: center;
          margin-bottom: 40px;
        }
        .logo {
          font-size: 32px;
          font-weight: bold;
          color: #8CFFDA;
          margin-bottom: 10px;
          text-shadow: 0 0 20px rgba(140, 255, 218, 0.5);
        }
        .subtitle {
          color: #7A5CFF;
          font-size: 16px;
          margin-bottom: 30px;
        }
        .content {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(140, 255, 218, 0.2);
          border-radius: 16px;
          padding: 30px;
          margin-bottom: 30px;
          backdrop-filter: blur(10px);
        }
        .welcome-title {
          font-size: 24px;
          color: #8CFFDA;
          margin-bottom: 20px;
          text-align: center;
        }
        .position-badge {
          background: linear-gradient(135deg, #7A5CFF, #8CFFDA);
          color: #0a0a0a;
          padding: 8px 16px;
          border-radius: 20px;
          font-weight: bold;
          display: inline-block;
          margin: 10px 0;
        }
        .feature-list {
          list-style: none;
          padding: 0;
          margin: 20px 0;
        }
        .feature-list li {
          padding: 8px 0;
          border-left: 3px solid #8CFFDA;
          padding-left: 15px;
          margin: 10px 0;
        }
        .cta-button {
          display: inline-block;
          background: linear-gradient(135deg, #8CFFDA, #7A5CFF);
          color: #0a0a0a;
          padding: 15px 30px;
          text-decoration: none;
          border-radius: 12px;
          font-weight: bold;
          margin: 20px 0;
          text-align: center;
          transition: all 0.3s ease;
        }
        .footer {
          text-align: center;
          color: #888;
          font-size: 14px;
          margin-top: 40px;
        }
        .spore {
          display: inline-block;
          width: 8px;
          height: 8px;
          background: #8CFFDA;
          border-radius: 50%;
          margin: 0 5px;
          opacity: 0.7;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <div class="logo">🍄 FUNGIO</div>
          <div class="subtitle">Your Messages Don't Just Travel—They Grow</div>
        </div>
        
        <div class="content">
          <h1 class="welcome-title">Your Spore Has Been Planted! 🌱</h1>
          
          <p>Welcome to the Fungio Beta community! You're now part of a living network that grows stronger with each connection.</p>
          
          <div style="text-align: center;">
            <span class="position-badge">Beta Cultivator #${position}</span>
          </div>
          
          <p>As an early cultivator, you'll help shape the future of decentralized communication. Here's what you can expect:</p>
          
          <ul class="feature-list">
            <li>🔒 <strong>Privacy-First Messaging:</strong> Your conversations grow through mycelial networks, not corporate servers</li>
            <li>🧠 <strong>Kaeluun Intelligence:</strong> Experience AI that learns and adapts without compromising your privacy</li>
            <li>🌐 <strong>Offline Resilience:</strong> Stay connected even when the internet fails</li>
            <li>🍄 <strong>Organic Growth:</strong> Watch your network expand naturally through spore propagation</li>
          </ul>
          
          <div style="text-align: center;">
            <a href="https://fungio.network" class="cta-button">Explore the Network</a>
          </div>
        </div>
        
        <div class="content">
          <h2 style="color: #7A5CFF; font-size: 20px;">What Happens Next?</h2>
          
          <p>🔬 <strong>Beta Testing Begins Soon:</strong> We'll notify you when the first beta version is ready for cultivation.</p>
          
          <p>📖 <strong>Read the Manifesto:</strong> Dive deeper into our vision for decentralized communication at <a href="https://fungio.network/whitepaper" style="color: #8CFFDA;">fungio.network/whitepaper</a></p>
          
          <p>🤝 <strong>Join the Community:</strong> Connect with other beta cultivators and share your thoughts on the future of private communication.</p>
        </div>
        
        <div class="footer">
          <div style="margin-bottom: 10px;">
            <span class="spore"></span>
            <span class="spore"></span>
            <span class="spore"></span>
          </div>
          <p>This message was grown in the Fungio network and delivered with care.</p>
          <p style="font-size: 12px; color: #666;">If you didn't sign up for Fungio Beta, you can safely ignore this email.</p>
        </div>
      </div>
    </body>
    </html>
  `;
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    const { email } = req.body;

    // Basic validation
    if (!email || !email.includes('@')) {
      return res.status(400).json({ message: 'Valid email is required' });
    }

    const signupData: BetaSignupData = {
      email: email.toLowerCase().trim(),
      timestamp: new Date().toISOString(),
    };

    // Create data directory if it doesn't exist
    const dataDir = path.join(process.cwd(), 'data');
    if (!fs.existsSync(dataDir)) {
      fs.mkdirSync(dataDir, { recursive: true });
    }

    // Read existing signups
    const signupsFile = path.join(dataDir, 'beta-signups.json');
    let signups: BetaSignupData[] = [];
    
    if (fs.existsSync(signupsFile)) {
      const fileContent = fs.readFileSync(signupsFile, 'utf8');
      signups = JSON.parse(fileContent);
    }

    // Check if email already exists
    const existingSignup = signups.find(signup => signup.email === signupData.email);
    if (existingSignup) {
      return res.status(409).json({ message: 'Email already registered for beta' });
    }

    // Add new signup
    signups.push(signupData);

    // Write back to file
    fs.writeFileSync(signupsFile, JSON.stringify(signups, null, 2));

    // Send welcome email via Resend
    await sendWelcomeEmail(signupData.email, signups.length);

    // Log signup for monitoring
    console.log(`New beta signup: ${signupData.email} at ${signupData.timestamp}`);

    return res.status(200).json({ 
      message: 'Successfully joined the beta waitlist! Check your email for next steps.',
      data: {
        email: signupData.email,
        position: signups.length
      }
    });

  } catch (error) {
    console.error('Beta signup error:', error);
    return res.status(500).json({ message: 'Internal server error' });
  }
}
