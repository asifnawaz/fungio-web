import { NextApiRequest, NextApiResponse } from 'next';
import fs from 'fs';
import path from 'path';

interface BetaSignupData {
  email: string;
  timestamp: string;
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

    // Log signup for monitoring
    console.log(`New beta signup: ${signupData.email} at ${signupData.timestamp}`);

    return res.status(200).json({ 
      message: 'Successfully joined the beta waitlist',
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
