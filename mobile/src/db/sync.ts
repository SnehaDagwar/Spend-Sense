import { synchronize } from '@nozbe/watermelondb/sync';
import { database } from './database';
import { apiClient } from '../services/apiClient';

export async function syncOfflineDatabase() {
  await synchronize({
    database,
    pullChanges: async ({ lastPulledAt, schemaVersion }) => {
      // Fetch changes from FastAPI server
      // Translate timestamp to Date object if needed
      const response = await apiClient.get(
        `/sync/pull?lastPulledAt=${lastPulledAt ? new Date(lastPulledAt).toISOString() : ''}`
      );
      
      const { changes, timestamp } = response;
      
      return { 
        changes, 
        timestamp: new Date(timestamp).getTime() 
      };
    },
    pushChanges: async ({ changes, lastPulledAt }) => {
      // Send modifications back to FastAPI
      await apiClient.post('/sync/push', {
        changes,
        lastPulledAt: new Date(lastPulledAt).toISOString(),
      });
    },
    sendCreatedAsUpdated: true,
  });
}
