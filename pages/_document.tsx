import { Html, Head, Main, NextScript } from 'next/document';

export default function Document() {
  return (
    <Html lang="en">
      <Head>
        {/* Favicon - using data URI for build-time generation */}
        <link 
          rel="icon" 
          type="image/svg+xml" 
          href="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAzMiAzMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8cGF0aCBkPSJNMTYgNEMxMC41IDQgNiA4LjUgNiAxNEM2IDE2IDcgMTcuNSA4LjUgMTguNUM5LjUgMTkgMTAuNSAxOSAxMS41IDE5SDIwLjVDMjEuNSAxOSAyMi41IDE5IDIzLjUgMTguNUMyNSAxNy41IDI2IDE2IDI2IDE0QzI2IDguNSAyMS41IDQgMTYgNFoiIGZpbGw9IiM4Q0ZGREEiIG9wYWNpdHk9IjAuOCIvPgogIDxyZWN0IHg9IjE0IiB5PSIxOCIgd2lkdGg9IjQiIGhlaWdodD0iMTAiIHJ4PSIyIiBmaWxsPSIjQTg1NUY3IiBvcGFjaXR5PSIwLjYiLz4KICA8Y2lyY2xlIGN4PSIxMCIgY3k9IjEyIiByPSIxIiBmaWxsPSIjOENGRkRBIiBvcGFjaXR5PSIwLjYiLz4KICA8Y2lyY2xlIGN4PSIyMiIgY3k9IjEwIiByPSIwLjgiIGZpbGw9IiNBODU1RjciIG9wYWNpdHk9IjAuNyIvPgogIDxjaXJjbGUgY3g9IjgiIGN5PSIxNiIgcj0iMC42IiBmaWxsPSIjOENGRkRBIiBvcGFjaXR5PSIwLjUiLz4KICA8Y2lyY2xlIGN4PSIyNCIgY3k9IjE2IiByPSIwLjciIGZpbGw9IiNBODU1RjciIG9wYWNpdHk9IjAuNiIvPgogIDxwYXRoIGQ9Ik0xMiAyMkw4IDI2TTE5IDIyTDI0IDI2TTE2IDI4TDEyIDMwTTE2IDI4TDIwIDMwIiBzdHJva2U9IiM4Q0ZGREEiIHN0cm9rZS13aWR0aD0iMSIgb3BhY2l0eT0iMC40IiBzdHJva2UtbGluZWNhcD0icm91bmQiLz4KPC9zdmc+" 
        />
        
        {/* Theme color */}
        <meta name="theme-color" content="#8CFFDA" />
        
        {/* Fonts */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link 
          href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap" 
          rel="stylesheet" 
        />
      </Head>
      <body>
        <Main />
        <NextScript />
      </body>
    </Html>
  );
}
