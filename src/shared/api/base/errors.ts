import type { AxiosError } from 'axios';

export class HttpError extends Error {
  readonly status: number;
  readonly statusText: string;
  readonly errorData: unknown;
  readonly originalError: AxiosError;

  constructor(error: AxiosError) {
    super(error.message);
    this.name = 'HttpError';
    this.status = error.response?.status ?? 0;
    this.statusText = error.response?.statusText ?? '';
    this.errorData = error.response?.data;
    this.originalError = error;
  }
}

export function logError(error: HttpError): void {
  console.error(`[API ${error.status}] ${error.message}`, error.errorData);
}
