import { NextApiRequest, NextApiResponse } from 'next';
import { Resend } from 'resend';

// Define type for Resend API error response
interface ResendError extends Error {
  statusCode?: number;
  name: string;
  message: string;
}

interface BetaSignupData {
  email: string;
  timestamp: string;
}

// Initialize Resend
const resend = new Resend(process.env.RESEND_API_KEY);

// Fungio Beta Audience ID - this should be created in your Resend dashboard
const BETA_AUDIENCE_ID = process.env.RESEND_BETA_AUDIENCE_ID;

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
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    console.log('Beta signup request received:', { body: req.body, method: req.method });
    
    const { email } = req.body;

    // Enhanced validation
    if (!email) {
      console.log('Validation failed: No email provided');
      return res.status(400).json({ message: 'Email is required' });
    }

    if (typeof email !== 'string' || !email.includes('@') || email.length < 5) {
      console.log('Validation failed: Invalid email format:', email);
      return res.status(400).json({ message: 'Valid email is required' });
    }

    // Debug log environment variables (don't log full API key in production)
    console.log('Resend Config:', {
      hasApiKey: !!process.env.RESEND_API_KEY,
      apiKeyPrefix: process.env.RESEND_API_KEY ? `${process.env.RESEND_API_KEY.substring(0, 5)}...` : 'none',
      hasAudienceId: !!BETA_AUDIENCE_ID,
      audienceIdPrefix: BETA_AUDIENCE_ID ? `${BETA_AUDIENCE_ID.substring(0, 5)}...` : 'none',
      nodeEnv: process.env.NODE_ENV
    });

    // Check if Resend is properly configured
    if (!process.env.RESEND_API_KEY) {
      const errorMsg = 'RESEND_API_KEY not configured';
      console.error(errorMsg);
      return res.status(500).json({ 
        message: 'Email service not configured',
        error: process.env.NODE_ENV === 'development' ? errorMsg : undefined
      });
    }

    if (!BETA_AUDIENCE_ID) {
      const errorMsg = 'RESEND_BETA_AUDIENCE_ID not configured';
      console.error(errorMsg);
      return res.status(500).json({ 
        message: 'Beta audience not configured',
        error: process.env.NODE_ENV === 'development' ? errorMsg : undefined
      });
    }

    const cleanEmail = email.toLowerCase().trim();
    console.log('Processing signup for:', cleanEmail);

    try {
      // Add contact to Resend Audience for beta signups
      console.log('Attempting to add contact to Resend audience:', { 
        email: cleanEmail, 
        audienceId: BETA_AUDIENCE_ID.substring(0, 5) + '...' 
      });
      
      const { data: contactData, error: contactError } = await resend.contacts.create({
        email: cleanEmail,
        unsubscribed: false,
        audienceId: BETA_AUDIENCE_ID,
      });

      if (contactError) {
        // Type assertion for Resend error response
        const resendError: ResendError = contactError;
        const errorDetails = {
          message: resendError.message,
          name: resendError.name,
          statusCode: resendError.statusCode,
        };
        
        console.error('Failed to create contact in Resend:', errorDetails);
        
        // Check if it's a duplicate email error
        if (resendError.message && resendError.message.includes('already exists')) {
          return res.status(409).json({ 
            message: 'Email already registered for beta',
            error: process.env.NODE_ENV === 'development' ? errorDetails : undefined
          });
        }
        
        // Handle specific Resend API errors
        if (resendError.statusCode === 401) {
          return res.status(500).json({ 
            message: 'Authentication failed. Please check your Resend API key.',
            error: process.env.NODE_ENV === 'development' ? errorDetails : undefined
          });
        }
        
        if (resendError.statusCode === 404) {
          return res.status(500).json({ 
            message: 'Beta audience not found. Please check your audience ID.',
            error: process.env.NODE_ENV === 'development' ? errorDetails : undefined
          });
        }
        
        return res.status(500).json({ 
          message: 'Failed to register for beta',
          error: process.env.NODE_ENV === 'development' ? errorDetails : undefined
        });
      }

      console.log('Successfully added contact to Resend audience:', contactData);

      // Get the current audience size to determine position
      let position = 1;
      try {
        const { data: audienceData, error: audienceError } = await resend.audiences.get(BETA_AUDIENCE_ID);
        if (!audienceError && audienceData) {
          // Note: Resend doesn't provide direct contact count, so we'll use a default or estimate
          position = Math.floor(Math.random() * 100) + 1; // Placeholder - you may want to track this differently
        }
      } catch (audienceError) {
        console.warn('Could not get audience data for position:', audienceError);
      }

      // Send welcome email via Resend
      try {
        await sendWelcomeEmail(cleanEmail, position);
        console.log('Welcome email sent successfully');
      } catch (emailError) {
        console.error('Failed to send welcome email, but signup still successful:', emailError);
        // Don't fail the signup if welcome email fails
      }

      // Log signup for monitoring
      console.log(`✅ New beta signup: ${cleanEmail} at ${new Date().toISOString()}`);

      return res.status(200).json({ 
        message: 'Successfully joined the beta waitlist! Check your email for next steps.',
        data: {
          email: cleanEmail,
          position: position,
          contactId: contactData?.id
        }
      });

    } catch (error) {
      const err = error as Error | ResendError;
      console.error('Resend API error:', {
        message: err.message,
        name: err.name,
        stack: process.env.NODE_ENV === 'development' ? err.stack : undefined,
        ...('statusCode' in err && { statusCode: (err as ResendError).statusCode })
      });
      
      return res.status(500).json({ 
        message: 'Failed to process beta signup',
        ...(process.env.NODE_ENV === 'development' && { 
          error: {
            message: err.message,
            ...('statusCode' in err && { statusCode: (err as ResendError).statusCode })
          }
        })
      });
    }

  } catch (error) {
    console.error('❌ Beta signup error:', error);
    
    // Return more specific error information in development
    const isDev = process.env.NODE_ENV === 'development';
    return res.status(500).json({ 
      message: 'Internal server error',
      ...(isDev && { error: error instanceof Error ? error.message : String(error) })
    });
  }
}
