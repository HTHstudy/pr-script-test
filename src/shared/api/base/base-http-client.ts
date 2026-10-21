import type {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  AxiosError,
  InternalAxiosRequestConfig,
} from 'axios';
import axios from 'axios';
import { HttpError, logError } from './errors';

/** 인터셉터 내부에서 사용하는 설정 타입 */
export type HttpConfig = InternalAxiosRequestConfig;

export class BaseHttpClient {
  protected axiosInstance: AxiosInstance;

  constructor(config?: AxiosRequestConfig) {
    this.axiosInstance = axios.create({
      timeout: 60 * 1000,
      headers: { 'Content-Type': 'application/json' },
      ...config,
    });
    this.setupInterceptors();
  }

  // ── 인터셉터 훅 (protected — 하위 클래스에서 override) ──

  protected onRequest(config: HttpConfig): HttpConfig {
    return config;
  }

  protected onRequestError(error: AxiosError): Promise<never> {
    return Promise.reject(error);
  }

  protected onResponse<T = unknown>(response: AxiosResponse<T>): AxiosResponse<T> {
    return response;
  }

  protected onResponseError(error: AxiosError): Promise<never> {
    const httpError = new HttpError(error);
    logError(httpError);
    return Promise.reject(httpError);
  }

  // ── 인터셉터 등록 (private — 생성자에서 1회 호출) ──

  private setupInterceptors(): void {
    this.axiosInstance.interceptors.request.use(
      (cfg: HttpConfig) => this.onRequest(cfg),
      (err: AxiosError) => this.onRequestError(err),
    );
    this.axiosInstance.interceptors.response.use(
      (res: AxiosResponse) => this.onResponse(res),
      (err: AxiosError) => this.onResponseError(err),
    );
  }

  // ── HTTP 래퍼 메서드 (response.data 언래핑) ──

  async get<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const res = await this.axiosInstance.get<T>(url, config);
    return res.data;
  }

  async post<T = unknown, B = unknown>(url: string, body?: B, config?: AxiosRequestConfig): Promise<T> {
    const res = await this.axiosInstance.post<T>(url, body, config);
    return res.data;
  }

  async put<T = unknown, B = unknown>(url: string, body?: B, config?: AxiosRequestConfig): Promise<T> {
    const res = await this.axiosInstance.put<T>(url, body, config);
    return res.data;
  }

  async patch<T = unknown, B = unknown>(url: string, body?: B, config?: AxiosRequestConfig): Promise<T> {
    const res = await this.axiosInstance.patch<T>(url, body, config);
    return res.data;
  }

  async delete<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const res = await this.axiosInstance.delete<T>(url, config);
    return res.data;
  }
}
