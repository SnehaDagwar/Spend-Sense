import { Model } from '@nozbe/watermelondb';
import { field, readonly, date } from '@nozbe/watermelondb/decorators';

export default class Goal extends Model {
  static table = 'goals';

  @field('name') name!: string;
  @field('icon') icon!: string;
  @field('target_amount') targetAmount!: number;
  @field('current_amount') currentAmount!: number;
  @field('monthly_contribution') monthlyContribution!: number;
  @field('target_date') targetDate?: string;
  @field('color') color?: string;

  @readonly @date('created_at') createdAt!: Date;
  @readonly @date('updated_at') updatedAt!: Date;
}
