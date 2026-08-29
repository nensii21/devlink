const { deleteUserAccount } = require('../controllers/accountController');
const AccountDeletionService = require('../services/accountDeletionService');

jest.mock('../services/accountDeletionService');

describe('Account Deletion Workflow Lifecycle Isolation Unit Tests', () => {
  let mockRequest;
  let mockResponse;

  beforeEach(() => {
    mockRequest = {
      user: { id: 8841 },
      body: { confirmText: 'DELETE PERMANENTLY' }
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

  test('should successfully complete account permanent teardowns when valid confirm parameters match', async () => {
    AccountDeletionService.executePermanentDeletion.mockResolvedValue(true);

    await deleteUserAccount(mockRequest, mockResponse);

    expect(mockResponse.statusCode).toBe(200);
    expect(mockResponse.clearCookie).getMockName() ? expect(mockResponse.clearCookie).toHaveBeenCalledWith('auth_token') : null;
    expect(AccountDeletionService.executePermanentDeletion).toHaveBeenCalledWith(8841);
  });

  test('should halt compilation blocks and emit 400 parameters errors when confirmation text is invalid', async () => {
    mockRequest.body.confirmText = 'incorrect_validation_text';

    await deleteUserAccount(mockRequest, mockResponse);

    expect(mockResponse.statusCode).toBe(400);
    expect(AccountDeletionService.executePermanentDeletion).not.toHaveBeenCalled();
  });
});
