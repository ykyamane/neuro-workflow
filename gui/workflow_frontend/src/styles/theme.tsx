import { extendTheme } from '@chakra-ui/react';
import { mode } from '@chakra-ui/theme-tools';

const theme = extendTheme({
  config: {
    initialColorMode: 'dark',
    useSystemColorMode: false,
  },
  colors: {
    brand: {
      50: '#e6f1ff',
      100: '#c0d7f7',
      200: '#99bdef',
      300: '#71a3e7',
      400: '#4a8adf',
      500: '#3070c6',
      600: '#25579b',
      700: '#183e70',
      800: '#0c2547',
      900: '#020d1f',
    },
  },
  styles: {
    global: (props: any) => ({
      body: {
        // dark: original gray.900 | light: OpenAI-inspired near-white
        bg: mode('#f7f7f8', 'gray.900')(props),
        color: mode('#1a1a1a', 'white')(props),
        margin: 0,
        padding: 0,
      },
    }),
  },
  components: {
    Button: {
      baseStyle: {
        fontWeight: 'normal',
        borderRadius: 'md',
      },
      defaultProps: {
        colorScheme: 'brand',
        variant: 'ghost',
      },
    },
    Heading: {
      baseStyle: {
        fontWeight: 'medium',
        letterSpacing: 'tight',
      },
    },
    Modal: {
      parts: ['dialog', 'header', 'body', 'footer', 'closeButton', 'overlay'],
      baseStyle: (props: any) => ({
        dialog: {
          bg: mode('white', 'gray.800')(props),
          color: mode('#1a1a1a', 'white')(props),
          borderRadius: 'md',
          boxShadow: 'xl',
        },
        overlay: {
          bg: 'blackAlpha.700',
        },
        header: {
          fontWeight: 'bold',
          borderBottomWidth: '1px',
          borderColor: mode('#e5e5e5', 'gray.700')(props),
        },
        body: {},
        footer: {
          borderTopWidth: '1px',
          borderColor: mode('#e5e5e5', 'gray.700')(props),
        },
        closeButton: {
          color: mode('gray.500', 'gray.400')(props),
          _hover: {
            color: mode('#1a1a1a', 'white')(props),
            bg: mode('blackAlpha.100', 'whiteAlpha.100')(props),
          },
        },
      }),
    },
  },
});

export default theme;
