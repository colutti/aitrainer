
class MarkdownService {
    reload() {} 
}

class MarkdownComponent {}

class MarkdownModule {
    static forRoot() {
        return {
            ngModule: MarkdownModule,
            providers: [{ provide: MarkdownService, useClass: MarkdownService }]
        };
    }
}

/* global module */
module.exports = {
  MarkdownService,
  MarkdownComponent,
  MarkdownModule,
  provideMarkdown: () => ({})
};
