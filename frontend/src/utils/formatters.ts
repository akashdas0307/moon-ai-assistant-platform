import { format, isToday, isYesterday } from 'date-fns';

export const formatTimestamp = (timestamp: string | Date): string => {
  const date = new Date(timestamp);
  if (isToday(date)) return format(date, 'h:mm a');
  if (isYesterday(date)) return `Yesterday ${format(date, 'h:mm a')}`;
  return format(date, 'MMM d, h:mm a');
};
