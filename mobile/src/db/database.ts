import { Database } from '@nozbe/watermelondb';
import SQLiteAdapter from '@nozbe/watermelondb/adapters/sqlite';

import schema from './schema';
import Category from './models/Category';
import Expense from './models/Expense';
import Budget from './models/Budget';
import Goal from './models/Goal';

// Set up SQLite Adapter
const adapter = new SQLiteAdapter({
  schema,
  // (Optional) Database name
  dbName: 'SpendSenseOffline',
});

// Create WatermelonDB instance
export const database = new Database({
  adapter,
  modelClasses: [
    Category,
    Expense,
    Budget,
    Goal,
  ],
});
