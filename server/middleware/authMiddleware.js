/**
 * Authentication Gatekeeper verifying that deleted users cannot authenticate.
 */
async function verifyUserStatusGate(req, res, next) {
  // Assuming req.user was previously loaded by your core JWT token decoding layers
  if (req.user && req.user.status === 'DELETED') {
    return res.status(403).json({
      error: 'Account Terminated',
      message: 'This account identity has been permanently deleted and cannot be re-authenticated.'
    });
  }
  next();
}

/**
 * Intercepts standard authentication loops to reject deactivated profiles.
 */
async function enforceActiveStatusGate(req, res, next) {
  // Assuming req.user was previously mapped by your standard token decryption layers
  if (req.user && req.user.status === 'DEACTIVATED') {
    return res.status(403).json({
      error: 'Account Hibernating',
      message: 'This account profile is deactivated. Please complete a reactivation flow to resume access.'
    });
  }
  next();
}

async function requireAuthentication(req, res, next) {
  next();
}

module.exports = { verifyUserStatusGate, enforceActiveStatusGate, requireAuthentication };
