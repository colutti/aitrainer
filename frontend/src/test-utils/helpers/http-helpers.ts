import {
  HttpTestingController,
  RequestMatch
} from '@angular/common/http/testing';

/**
 * Helper para simplificar testes com HttpTestingController
 */
export class HttpTestHelper {
  constructor(private httpMock: HttpTestingController) {}

  /**
   * Verifica que uma requisição foi feita e retorna a resposta
   */
  expectAndRespond<T>(
    method: string,
    url: string | RegExp,
    response: T,
    statusCode: number = 200
  ): T {
    const request = this.httpMock.expectOne(
      typeof url === 'string' ? url : (req) => url.test(req.url)
    );

    expect(request.request.method).toBe(method);
    request.flush(response, { status: statusCode, statusText: 'OK' });

    return response;
  }

  /**
   * Simula um erro HTTP
   */
  expectAndError(
    method: string,
    url: string | RegExp,
    statusCode: number = 500,
    statusText: string = 'Server Error',
    errorBody: any = {}
  ): void {
    const request = this.httpMock.expectOne(
      typeof url === 'string' ? url : (req) => url.test(req.url)
    );

    expect(request.request.method).toBe(method);
    request.flush(errorBody, { status: statusCode, statusText });
  }

  /**
   * Simula um erro de rede
   */
  expectAndNetworkError(
    method: string,
    url: string | RegExp
  ): void {
    const request = this.httpMock.expectOne(
      typeof url === 'string' ? url : (req) => url.test(req.url)
    );

    expect(request.request.method).toBe(method);
    request.error(new ProgressEvent('Network error'));
  }

  /**
   * Verifica o corpo da requisição
   */
  expectRequestBody(
    method: string,
    url: string | RegExp,
    expectedBody: any
  ): any {
    const request = this.httpMock.expectOne(
      typeof url === 'string' ? url : (req) => url.test(req.url)
    );

    expect(request.request.body).toEqual(expectedBody);
    return request;
  }

  /**
   * Verifica os parâmetros de query
   */
  expectQueryParams(
    url: string | RegExp,
    expectedParams: { [key: string]: string }
  ): void {
    const request = this.httpMock.expectOne(
      typeof url === 'string' ? url : (req) => url.test(req.url)
    );

    Object.entries(expectedParams).forEach(([key, value]) => {
      expect(request.request.params.get(key)).toBe(value);
    });
  }

  /**
   * Aguarda nenhuma requisição pendente
   */
  verifyNoPendingRequests(): void {
    this.httpMock.verify();
  }
}
