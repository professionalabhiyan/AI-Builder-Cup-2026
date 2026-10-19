import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1';

  login(email: string, password: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/auth/login/`, { email, password });
  }

  setup2FA(preAuthToken: string): Observable<any> {
    const headers = new HttpHeaders({ 'X-Pre-Auth-Token': preAuthToken });
    return this.http.post(`${this.baseUrl}/auth/2fa/setup/`, { pre_auth_token: preAuthToken }, { headers });
  }

  verify2FA(preAuthToken: string, otpCode: string): Observable<any> {
    // Preserves leading zeros by ensuring string serialization
    const sanitizedOtp = String(otpCode).trim().padStart(6, '0');
    const headers = new HttpHeaders({ 'X-Pre-Auth-Token': preAuthToken });
    return this.http.post(
      `${this.baseUrl}/auth/2fa/verify/`,
      { pre_auth_token: preAuthToken, otp_code: sanitizedOtp },
      { headers }
    );
  }
}
