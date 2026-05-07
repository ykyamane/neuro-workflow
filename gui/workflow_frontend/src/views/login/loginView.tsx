import React, { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardBody,
  CardHeader,
  Center,
  Container,
  Heading,
  Icon,
  Spinner,
  Text,
  VStack,
} from '@chakra-ui/react';
import { LockIcon } from '@chakra-ui/icons';
import { useAuth } from '../../auth/authContext';

const LoginView: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { signIn, loading, user } = useAuth();

  useEffect(() => {
    if (user && !loading) {
      const from = (location.state as any)?.from?.pathname || '/';
      navigate(from, { replace: true });
    }
  }, [user, loading, navigate, location.state]);

  const bgGradient = 'linear(to-br, gray.900, brand.900, gray.800)';
  const cardBg = 'gray.800';
  const headerBg = 'linear(to-r, brand.600, brand.700)';

  if (loading) {
    return (
      <Box
        minH="100vh"
        bgGradient={bgGradient}
        display="flex"
        alignItems="center"
        justifyContent="center"
      >
        <Spinner size="xl" color="brand.500" />
      </Box>
    );
  }

  return (
    <Box
      minH="100vh"
      bgGradient={bgGradient}
      display="flex"
      alignItems="center"
      justifyContent="center"
      p={4}
      position="fixed"
      top="0"
      left="0"
      right="0"
      bottom="0"
      zIndex="1000"
    >
      <Container maxW="md">
        <Card
          bg={cardBg}
          shadow="2xl"
          borderRadius="2xl"
          overflow="hidden"
          border="1px"
          borderColor="gray.700"
        >
          <CardHeader bgGradient={headerBg} color="white" textAlign="center" py={8}>
            <Center mb={4}>
              <Box
                bg="gray.800"
                borderRadius="full"
                p={4}
                shadow="lg"
                border="2px"
                borderColor="gray.600"
              >
                <Icon as={LockIcon} w={8} h={8} color="brand.400" />
              </Box>
            </Center>
            <Heading size="xl">Sign In</Heading>
          </CardHeader>

          <CardBody p={8}>
            <VStack spacing={6}>
              <Text color="gray.400" textAlign="center">
                You will be redirected to the identity provider to sign in.
              </Text>
              <Button
                colorScheme="brand"
                size="lg"
                w="full"
                bg="brand.600"
                color="white"
                _hover={{ bg: 'brand.700' }}
                onClick={() => signIn()}
              >
                Continue to Sign In
              </Button>
            </VStack>
          </CardBody>
        </Card>
      </Container>
    </Box>
  );
};

export default LoginView;
