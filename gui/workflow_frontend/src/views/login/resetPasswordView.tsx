import React, { useState, ChangeEvent, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardBody,
  CardHeader,
  Center,
  Container,
  FormControl,
  FormErrorMessage,
  FormLabel,
  Heading,
  Icon,
  Input,
  InputGroup,
  InputLeftElement,
  InputRightElement,
  Text,
  VStack,
  Alert,
  AlertIcon,
  AlertDescription,
  Spinner,
  useToast,
} from '@chakra-ui/react';
import { LockIcon, ViewIcon, ViewOffIcon } from '@chakra-ui/icons';
import { authService } from '../../auth/authService';

const ResetPasswordView: React.FC = () => {
  const navigate = useNavigate();
  const toast = useToast();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<{ password?: string; confirm?: string; general?: string }>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [sessionReady, setSessionReady] = useState(false);

  useEffect(() => {
    const checkSession = async () => {
      await authService.getSession();
      setSessionReady(true);
    };
    checkSession();
  }, []);

  const validate = () => {
    const next: typeof errors = {};
    if (!password || password.length < 6) {
      next.password = 'Password must be at least 6 characters';
    }
    if (password !== confirmPassword) {
      next.confirm = 'Passwords do not match';
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) return;
    setIsSubmitting(true);
    setErrors({});
    try {
      const result = await authService.updatePassword(password);
      if (result.success) {
        toast({
          title: 'Password updated',
          description: 'You can now sign in with your new password.',
          status: 'success',
          duration: 5000,
          isClosable: true,
        });
        navigate('/login', { replace: true });
      } else {
        setErrors({ general: result.error?.message ?? 'Failed to update password' });
      }
    } catch {
      setErrors({ general: 'An unexpected error occurred' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const bgGradient = 'linear(to-br, gray.900, brand.900, gray.800)';
  const cardBg = 'gray.800';
  const headerBg = 'linear(to-r, brand.600, brand.700)';

  if (!sessionReady) {
    return (
      <Box minH="100vh" bgGradient={bgGradient} display="flex" alignItems="center" justifyContent="center">
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
    >
      <Container maxW="md">
        <Card bg={cardBg} shadow="2xl" borderRadius="2xl" overflow="hidden" border="1px" borderColor="gray.700">
          <CardHeader bgGradient={headerBg} color="white" textAlign="center" py={8}>
            <Center mb={4}>
              <Box bg="gray.800" borderRadius="full" p={4} shadow="lg" border="2px" borderColor="gray.600">
                <Icon as={LockIcon} w={8} h={8} color="brand.400" />
              </Box>
            </Center>
            <Heading size="xl" mb={2}>
              Set new password
            </Heading>
            <Text fontSize="sm" color="gray.300">
              Enter your new password below.
            </Text>
          </CardHeader>
          <CardBody p={8}>
            <VStack spacing={6}>
              {errors.general && (
                <Alert status="error" bg="red.900" color="white" borderRadius="md">
                  <AlertIcon />
                  <AlertDescription>{errors.general}</AlertDescription>
                </Alert>
              )}
              <FormControl isInvalid={!!errors.password}>
                <FormLabel color="white">New password</FormLabel>
                <InputGroup>
                  <InputLeftElement>
                    <LockIcon color="gray.400" marginTop={1.5} />
                  </InputLeftElement>
                  <Input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
                    placeholder="At least 6 characters"
                    size="lg"
                    focusBorderColor="brand.500"
                    color="white"
                    bg="gray.700"
                    borderColor="gray.600"
                    _placeholder={{ color: 'gray.400' }}
                  />
                  <InputRightElement>
                    <Button
                      variant="ghost"
                      size="sm"
                      marginTop={2}
                      onClick={() => setShowPassword(!showPassword)}
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? <ViewOffIcon /> : <ViewIcon />}
                    </Button>
                  </InputRightElement>
                </InputGroup>
                <FormErrorMessage>{errors.password}</FormErrorMessage>
              </FormControl>
              <FormControl isInvalid={!!errors.confirm}>
                <FormLabel color="white">Confirm password</FormLabel>
                <InputGroup>
                  <InputLeftElement>
                    <LockIcon color="gray.400" marginTop={1.5} />
                  </InputLeftElement>
                  <Input
                    type={showPassword ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm new password"
                    size="lg"
                    focusBorderColor="brand.500"
                    color="white"
                    bg="gray.700"
                    borderColor="gray.600"
                    _placeholder={{ color: 'gray.400' }}
                  />
                </InputGroup>
                <FormErrorMessage>{errors.confirm}</FormErrorMessage>
              </FormControl>
              <Button
                colorScheme="brand"
                size="lg"
                w="full"
                bg="brand.600"
                color="white"
                _hover={{ bg: 'brand.700' }}
                onClick={handleSubmit}
                isLoading={isSubmitting}
                loadingText="Updating..."
              >
                Update password
              </Button>
              <Button variant="link" color="gray.400" onClick={() => navigate('/login')} _hover={{ color: 'white' }}>
                Back to sign in
              </Button>
            </VStack>
          </CardBody>
        </Card>
      </Container>
    </Box>
  );
};

export default ResetPasswordView;
