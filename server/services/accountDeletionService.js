const { getDbConnection } = require('../config/database');
const Redis = require('ioredis');

const redisClient = new Redis(process.env.REDIS_URL || 'redis://127.0.0.1:6379');

class AccountDeletionService {
  /**
   * Orchestrates the secure erasure of a user profile and all corresponding resource dependencies.
   */
  static async executePermanentDeletion(userId) {
    const db = await getDbConnection();
    
    // Initiate transactional protection to guarantee atomic execution safety
    await db.beginTransaction();

    try {
      // 1. Retention Rules Cleanup: Purge data stores matching documented compliance metrics
      // Delete user-owned session logs and social relation dependencies
      await db.execute('DELETE FROM user_sessions WHERE user_id = ?', [userId]);
      await db.execute('DELETE FROM user_follows WHERE follower_id = ? OR following_id = ?', [userId, userId]);
      
      // Cascade clear user-owned operational resource metrics (e.g. customized study planners or quiz logs)
      await db.execute('DELETE FROM user_quiz_records WHERE user_id = ?', [userId]);

      // 2. Soft-Anonymize or hard delete the core user identity record
      // Setting status to 'DELETED' flags future auth loops to reject connection tokens
      await db.execute(
        "UPDATE users SET status = 'DELETED', email = CONCAT('deleted_', ?, '@openprep.internal'), password_hash = 'DEACTIVATED' WHERE id = ?",
        [Date.now(), userId]
      );

      // 3. Clear Session Registries: Evict active tracking values out of Redis storage
      // Find and terminate active session cache handles linked to this account identity
      const activeSessionKeys = await redisClient.keys(`session:active:*:${userId}`);
      if (activeSessionKeys.length > 0) {
        await redisClient.del(...activeSessionKeys);
      }

      // Commit full changes cleanly
      await db.commit();
      return true;

    } catch (error) {
      // Rollback database mutations if any cascade block fails to prevent partial/corrupted user records
      await db.rollback();
      console.error(`Account erasure transaction failed for user ID ${userId}:`, error);
      throw error;
    }
  }
}

module.exports = AccountDeletionService;
