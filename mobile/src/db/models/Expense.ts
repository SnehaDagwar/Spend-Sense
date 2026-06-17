import { Model } from '@nozbe/watermelondb';
import { field, readonly, date } from '@nozbe/watermelondb/decorators';

export default class Expense extends Model {
  static table = 'expenses';

  @field('category_id') categoryId!: string;
  @field('amount') amount!: number;
  @field('date') date!: string;
  @field('note') note!: string;
  @field('month') month!: string;
  @field('payment_method') paymentMethod?: string;
  @field('merchant') merchant?: string;
  @field('currency') currency!: string;
  @field('is_recurring') isRecurring!: boolean;

  @readonly @date('created_at') createdAt!: Date;
  @readonly @date('updated_at') updatedAt!: Date;
}
