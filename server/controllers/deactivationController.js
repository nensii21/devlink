const DeactivationModel = require('../models/deactivationModel');
const bcrypt = require('bcryptjs');

/**
 * Puts an active user profile into a deactivated hibernation state.
 */
async function deactivateAccount(req, res) {
  try {
    const userId = req.user.id; // From your active verification session middleware token

    await DeactivationModel.updateAccountStatus(userId, 'DEACTIVATED');

    // Force evict browser session states
    res.clearCookie('auth_token');

    return res.status(200).json({
      status: 'DEACTIVATED',
      message: 'Your account has been deactivated successfully. Your data is preserved, but your public profile is hidden.'
    });
  } catch (error) {
    console.error('Deactivation processing pipeline error:', error);
    return res.status(500).json({ message: 'Internal Server Error processing deactivation parameters.' });
  }
}

/**
 * Handles explicit account restoration / reactivation.
 */
async function reactivateAccount(req, res) {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ message: 'Missing parameters: Email and password are required.' });
    }

    const user = await DeactivationModel.findUserByEmail(email);
    if (!user || user.status !== 'DEACTIVATED') {
      return res.status(404).json({ message: 'Resource Error: No deactivated profile matches this email.' });
    }

    // Verify access parameters safely
    const isMatch = await bcrypt.compare(password, user.password_hash);
    if (!isMatch) {
      return res.status(401).json({ message: 'Authentication Failed: Invalid password credentials.' });
    }

    // Toggle status parameters back to ACTIVE operational status
    await DeactivationModel.updateAccountStatus(user.id, 'ACTIVE');

    return res.status(200).json({
      status: 'ACTIVE',
      message: 'Welcome back! Your account has been reactivated successfully, and your profile is visible again.'
    });
  } catch (error) {
    console.error('Reactivation processing pipeline error:', error);
    return res.status(500).json({ message: 'Internal Server Error processing reactivation updates.' });
  }
}

module.exports = { deactivateAccount, reactivateAccount };
