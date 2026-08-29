const express = require('express');
const router = express.Router();
const { deactivateAccount, reactivateAccount } = require('../controllers/deactivationController');
const { requireAuthentication } = require('../middleware/authMiddleware');

router.post('/account/deactivate', requireAuthentication, deactivateAccount);
router.post('/account/reactivate', reactivateAccount); // Open path executing raw credentials checks

module.exports = router;
