import { Model } from '@nozbe/watermelondb';
import { field, readonly, date } from '@nozbe/watermelondb/decorators';

export default class Category extends Model {
  static table = 'categories';

  @field('slug') slug!: string;
  @field('name') name!: string;
  @field('icon') icon!: string;
  @field('color') color!: string;
  @field('display_order') displayOrder!: number;
  @field('is_system') isSystem!: boolean;

  @readonly @date('created_at') createdAt!: Date;
  @readonly @date('updated_at') updatedAt!: Date;
}
