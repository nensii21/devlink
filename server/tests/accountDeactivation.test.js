const { deactivateAccount, reactivateAccount } = require('../controllers/deactivationController');
const DeactivationModel = require('../models/deactivationModel');
const bcrypt = require('bcryptjs');

jest.mock('../models/deactivationModel');
jest.mock('bcryptjs');

describe('Account Deactivation/Reactivation System Unit Tests', () => {
  let mockRequest;
  let mockResponse;

  beforeEach(() => {
    mockRequest = {
      user: { id: 7041 },
      body: {}
    };

    mockResponse = {
      statusCode: 200,
      headers: {},
      status: function(code) { this.statusCode = code; return this; },
      json: function(data) { this.body = data; return this; },
      clearCookie: jest.fn()
    };

    jest.clearAllMocks();
  });

  test('should successfully transition account to deactivation states and clear token cookies', async () => {
    DeactivationModel.updateAccountStatus.mockResolvedValue(true);

    await deactivateAccount(mockRequest, mockResponse);

    expect(mockResponse.statusCode).toBe(200);
    expect(mockResponse.body.status).toBe('DEACTIVATED');
    expect(mockResponse.clearCookie).toHaveBeenCalledWith('auth_token');
    expect(DeactivationModel.updateAccountStatus).toHaveBeenCalledWith(7041, 'DEACTIVATED');
  });

  test('should verify credentials and restore profile access on valid reactivation queries', async () => {
    mockRequest.body = { email: 'test@openprep.ai', password: 'secure_password_101' };
    
    DeactivationModel.findUserByEmail.mockResolvedValue({
      id: 7041,
      email: 'test@openprep.ai',
      password_hash: 'hashed_string',
      status: 'DEACTIVATED'
    });
    bcrypt.compare.mockResolvedValue(true); // Password match verification success
    DeactivationModel.updateAccountStatus.mockResolvedValue(true);

    await reactivateAccount(mockRequest, mockResponse);

    expect(mockResponse.statusCode).toBe(200);
    expect(mockResponse.body.status).toBe('ACTIVE');
    expect(DeactivationModel.updateAccountStatus).toHaveBeenCalledWith(7041, 'ACTIVE');
  });
});
