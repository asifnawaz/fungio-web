import type { NextApiRequest, NextApiResponse } from 'next';
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);
const audienceId = process.env.AUDIENCE_ID;

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  const { email } = req.body;

  if (!email || typeof email !== 'string') {
    return res.status(400).json({ error: 'Email is required' });
  }

  if (!audienceId) {
    console.error('AUDIENCE_ID is not set in environment variables.');
    return res.status(500).json({ error: 'Server configuration error.' });
  }

  try {
    await resend.contacts.create({
      email: email,
      audienceId: audienceId,
    });

    return res.status(201).json({ success: true });
  } catch (error) {
    console.error(error);
    if (error instanceof Error) {
        return res.status(500).json({ error: error.message });
    }
    return res.status(500).json({ error: 'An unknown error occurred' });
  }
}
