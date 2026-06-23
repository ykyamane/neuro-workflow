import React from 'react';
import {
  Badge,
  Box,
  Button,
  Card,
  CardBody,
  CardHeader,
  Code,
  Divider,
  Flex,
  HStack,
  Heading,
  SimpleGrid,
  Stack,
  Tag,
  Text,
  VStack,
  useColorModeValue,
} from '@chakra-ui/react';
import { ExternalLinkIcon } from '@chakra-ui/icons';
import type { KeycloakProfile, KeycloakTokenParsed } from 'keycloak-js';
import { getAccountConsoleUrl, getKeycloak } from '../../auth/keycloak';

const Field: React.FC<{ label: string; children: React.ReactNode }> = ({
  label,
  children,
}) => {
  const labelColor = useColorModeValue('gray.600', 'gray.400');
  return (
    <Box>
      <Text fontSize="xs" textTransform="uppercase" color={labelColor} mb={1}>
        {label}
      </Text>
      <Box fontSize="sm">{children}</Box>
    </Box>
  );
};

const SectionCard: React.FC<{ title: string; children: React.ReactNode }> = ({
  title,
  children,
}) => {
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  return (
    <Card bg={cardBg} borderWidth="1px" borderColor={borderColor} shadow="sm">
      <CardHeader pb={2}>
        <Heading size="sm">{title}</Heading>
      </CardHeader>
      <Divider borderColor={borderColor} />
      <CardBody>{children}</CardBody>
    </Card>
  );
};

const UserProfileView: React.FC = () => {
  const pageBg = useColorModeValue('#f7f7f8', 'gray.900');

  const kc = getKeycloak();
  const tokenParsed = kc.tokenParsed as KeycloakTokenParsed | undefined;

  const profile: KeycloakProfile | null = tokenParsed ? {
    id: tokenParsed.sub,
    username: tokenParsed.preferred_username,
    email: tokenParsed.email as string | undefined,
    emailVerified: tokenParsed.email_verified as boolean | undefined,
    firstName: tokenParsed.given_name as string | undefined,
    lastName: tokenParsed.family_name as string | undefined,
    enabled: true,
    attributes: {},
  } : null;

  const attributeEntries: [string, string[]][] = [];

  const fullName = [profile?.firstName, profile?.lastName]
    .filter(Boolean)
    .join(' ')
    .trim();

  return (
    <Box height="100%" width="100%" overflow="auto" bg={pageBg}>
      <VStack
        spacing={4}
        width="100%"
        p={6}
        maxWidth="900px"
        mx="auto"
        minHeight="100vh"
        align="stretch"
      >
        <Flex justify="space-between" align="center" mb={2} wrap="wrap" gap={3}>
          <Heading size="lg">User Profile</Heading>
          <HStack>
            <Button
              size="sm"
              colorScheme="brand"
              rightIcon={<ExternalLinkIcon />}
              as="a"
              href={getAccountConsoleUrl()}
              target="_blank"
              rel="noopener noreferrer"
            >
              Manage account
            </Button>
          </HStack>
        </Flex>

        <VStack align="stretch" spacing={4}>
            <SectionCard title="Identity">
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                <Field label="User ID (sub)">
                  <Code fontSize="xs" wordBreak="break-all" px={2} py={1}>
                    {profile?.id ?? tokenParsed?.sub ?? '—'}
                  </Code>
                </Field>
                <Field label="Username">
                  <Text>{profile?.username ?? tokenParsed?.preferred_username ?? '—'}</Text>
                </Field>
                <Field label="Email">
                  <HStack>
                    <Text>{profile?.email ?? '—'}</Text>
                    {profile?.email && (
                      <Badge colorScheme={profile.emailVerified ? 'green' : 'yellow'}>
                        {profile.emailVerified ? 'Verified' : 'Unverified'}
                      </Badge>
                    )}
                  </HStack>
                </Field>
                <Field label="Status">
                  <Badge colorScheme={profile?.enabled === false ? 'red' : 'green'}>
                    {profile?.enabled === false ? 'Disabled' : 'Enabled'}
                  </Badge>
                </Field>
              </SimpleGrid>
            </SectionCard>

            <SectionCard title="Name">
              <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
                <Field label="First name">
                  <Text>{profile?.firstName || '—'}</Text>
                </Field>
                <Field label="Last name">
                  <Text>{profile?.lastName || '—'}</Text>
                </Field>
                <Field label="Full name">
                  <Text>{fullName || '—'}</Text>
                </Field>
              </SimpleGrid>
            </SectionCard>

            {attributeEntries.length > 0 && (
              <SectionCard title="Custom attributes">
                <Stack spacing={3} divider={<Divider />}>
                  {attributeEntries.map(([key, values]) => (
                    <Flex key={key} gap={3} wrap="wrap">
                      <Text fontWeight="semibold" minW="160px">
                        {key}
                      </Text>
                      <Box flex="1">
                        {values.map((v, i) => (
                          <Tag key={`${key}-${i}`} mr={1} mb={1}>
                            {v}
                          </Tag>
                        ))}
                      </Box>
                    </Flex>
                  ))}
                </Stack>
              </SectionCard>
            )}
          </VStack>
      </VStack>
    </Box>
  );
};

export default UserProfileView;
