import { appSchema, tableSchema } from '@nozbe/watermelondb';

export default appSchema({
  version: 1,
  tables: [
    tableSchema({
      name: 'categories',
      columns: [
        { name: 'slug', type: 'string' },
        { name: 'name', type: 'string' },
        { name: 'icon', type: 'string' },
        { name: 'color', type: 'string' },
        { name: 'display_order', type: 'number' },
        { name: 'is_system', type: 'boolean' },
        { name: 'created_at', type: 'number' },
        { name: 'updated_at', type: 'number' },
      ],
    }),
    tableSchema({
      name: 'expenses',
      columns: [
        { name: 'category_id', type: 'string', isIndexed: true },
        { name: 'amount', type: 'number' },
        { name: 'date', type: 'string' },
        { name: 'note', type: 'string' },
        { name: 'month', type: 'string', isIndexed: true },
        { name: 'payment_method', type: 'string', isOptional: true },
        { name: 'merchant', type: 'string', isOptional: true },
        { name: 'currency', type: 'string' },
        { name: 'is_recurring', type: 'boolean' },
        { name: 'created_at', type: 'number' },
        { name: 'updated_at', type: 'number' },
      ],
    }),
    tableSchema({
      name: 'budgets',
      columns: [
        { name: 'month', type: 'string', isIndexed: true },
        { name: 'income', type: 'number' },
        { name: 'created_at', type: 'number' },
        { name: 'updated_at', type: 'number' },
      ],
    }),
    tableSchema({
      name: 'goals',
      columns: [
        { name: 'name', type: 'string' },
        { name: 'icon', type: 'string' },
        { name: 'target_amount', type: 'number' },
        { name: 'current_amount', type: 'number' },
        { name: 'monthly_contribution', type: 'number' },
        { name: 'target_date', type: 'string', isOptional: true },
        { name: 'color', type: 'string', isOptional: true },
        { name: 'created_at', type: 'number' },
        { name: 'updated_at', type: 'number' },
      ],
    }),
  ],
});
