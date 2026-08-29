const AccountDeletionService = require('../services/accountDeletionService');

/**
 * Validates credentials, clears account tokens, and terminates user identity access maps.
 */
async function deleteUserAccount(req, res) {
  try {
    // Acceptance Criteria: Deletion requires authenticated user profile confirmation
    const authenticatedUserId = req.user.id;

    if (!authenticatedUserId) {
      return res.status(401).json({ message: 'Access Denied: Valid active authentication token required.' });
    }

    // Optional safety flag check: require an explicit text verification validation if necessary
    const { confirmText } = req.body;
    if (confirmText !== 'DELETE PERMANENTLY') {
      return res.status(400).json({ 
        message: 'Validation Failed: Input parameter text verification mismatch.' 
      });
    }

    await AccountDeletionService.executePermanentDeletion(authenticatedUserId);

    // Explicitly un-decorate outbound client browser cookie tokens if running cookie sessions
    res.clearCookie('auth_token');

    return res.status(200).json({
      status: 'TERMINATED',
      message: 'Your account identity has been permanently erased alongside all custom application cache metadata allocations.'
    });

  } catch (error) {
    console.error('Account termination controller processing exception:', error);
    return res.status(500).json({ message: 'Internal Server Error executing account deletion routing pipelines.' });
  }
}

module.exports = { deleteUserAccount };
