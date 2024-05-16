import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { OAuthService, AuthConfig } from 'angular-oauth2-oidc';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private tokenUrl = 'https://login.microsoftonline.com/2cda5d11-f0ac-46b3-967d-af1b2e1bd01a/oauth2/v2.0/token';
  private apiUrl = 'https://atlas.api.sbb.ch/prm-directory/v1/relations';
  private clientId = 'b04f9592-53f3-42ba-81a1-0f3a37411b23';
  private clientSecret = 'q938Q~vCsvRdSzdEVXqUvKo_3CL5XBjhX.CQjcrS';
  private scope = 'api://f3cdcb3e-1e95-4591-b664-4526d00f5d66/.default';

  constructor(private http: HttpClient, private oauthService: OAuthService) {
    this.initAuth();
  }

  private initAuth() {
    const authConfig: AuthConfig = {
      issuer: 'https://login.microsoftonline.com/{tenantId}/v2.0',
      clientId: this.clientId,
      dummyClientSecret: this.clientSecret,
      redirectUri: window.location.origin,
      responseType: 'code',
      scope: this.scope,
      showDebugInformation: true,
    };
    this.oauthService.configure(authConfig);
    this.oauthService.loadDiscoveryDocumentAndLogin();
  }

  public login() {
    this.oauthService.initLoginFlow();
  }

  public logout() {
    this.oauthService.logOut();
  }

  public get token() {
    return this.oauthService.getAccessToken();
  }

  public get isLoggedIn() {
    return this.oauthService.hasValidAccessToken();
  }

  getToken(): Observable<any> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/x-www-form-urlencoded'
    });
    const body = `grant_type=client_credentials&client_id=${this.clientId}&client_secret=${this.clientSecret}&scope=${encodeURIComponent(this.scope)}`;
    return this.http.post(this.tokenUrl, body, { headers });
  }

  fetchData(referencePointSloids: string, size: number): Observable<any> {
    const headers = new HttpHeaders({
      'Authorization': `Bearer ${this.token}`,
      'Content-Type': 'application/json'
    });
    return this.http.get(`${this.apiUrl}/endpoint`, { headers });
  }
}
