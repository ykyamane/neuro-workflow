import React, { useCallback, useEffect, useState } from 'react';
import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Alert,
  AlertDescription,
  AlertIcon,
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
  Spinner,
  Stack,
  Tag,
  Text,
  VStack,
  useColorModeValue,
} from '@chakra-ui/react';
import { ExternalLinkIcon, RepeatIcon } from '@chakra-ui/icons';
import type { KeycloakProfile, KeycloakTokenParsed } from 'keycloak-js';
import {
  getAccountConsoleUrl,
  getKeycloak,
  getKeycloakClientId,
} from '../../auth/keycloak';

const KNOWN_PROFILE_KEYS: ReadonlyArray<keyof KeycloakProfile> = [
  'id',
  'username',
  'email',
  'firstName',
  'lastName',
  'emailVerified',
  'enabled',
  'totp',
  'createdTimestamp',
  'attributes',
];

const formatTimestamp = (ms?: number): string => {
  if (!ms) return '—';
  const d = new Date(ms);
  return Number.isNaN(d.getTime()) ? '—' : d.toLocaleString();
};

const collectRoles = (token: KeycloakTokenParsed | undefined) => {
  const realmRoles = (token?.realm_access?.roles ?? []) as string[];
  const resourceAccess = (token?.resource_access ?? {}) as Record<
    string,
    { roles?: string[] }
  >;
  const clientRoles: { client: string; role: string }[] = [];
  for (const [client, value] of Object.entries(resourceAccess)) {
    for (const role of value.roles ?? []) {
      clientRoles.push({ client, role });
    }
  }
  return { realmRoles, clientRoles };
};

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
  const [profile, setProfile] = useState<KeycloakProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const pageBg = useColorModeValue('#f7f7f8', 'gray.900');
  const mutedColor = useColorModeValue('gray.600', 'gray.400');
  const codeBg = useColorModeValue('gray.50', 'gray.900');

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const kc = getKeycloak();
      const result = await kc.loadUserProfile();
      setProfile(result);
    } catch (e) {
      console.error('Failed to load Keycloak user profile:', e);
      setError('Failed to load user profile from Keycloak.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const kc = getKeycloak();
  const tokenParsed = kc.tokenParsed as KeycloakTokenParsed | undefined;
  const { realmRoles, clientRoles } = collectRoles(tokenParsed);
  const clientId = getKeycloakClientId();
  const ownClientRoles = clientRoles.filter((r) => r.client === clientId);
  const otherClientRoles = clientRoles.filter((r) => r.client !== clientId);

  const attributes = (profile?.attributes ?? {}) as Record<string, string[]>;
  const attributeEntries = Object.entries(attributes);

  const extraProfileEntries = profile
    ? Object.entries(profile).filter(
        ([k]) => !KNOWN_PROFILE_KEYS.includes(k as keyof KeycloakProfile),
      )
    : [];

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
              leftIcon={<RepeatIcon />}
              variant="outline"
              onClick={load}
              isLoading={loading}
            >
              Refresh
            </Button>
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

        {error && (
          <Alert status="error" mb={4} borderRadius="md">
            <AlertIcon />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {loading && !profile ? (
          <Flex justify="center" py={20}>
            <Spinner size="lg" />
          </Flex>
        ) : (
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

            <SectionCard title="Account metadata">
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                <Field label="Created">
                  <Text>{formatTimestamp(profile?.createdTimestamp)}</Text>
                </Field>
                <Field label="TOTP enabled">
                  <Badge colorScheme={profile?.totp ? 'green' : 'gray'}>
                    {profile?.totp ? 'Yes' : 'No'}
                  </Badge>
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

            {extraProfileEntries.length > 0 && (
              <SectionCard title="Other profile fields">
                <Stack spacing={3} divider={<Divider />}>
                  {extraProfileEntries.map(([key, value]) => (
                    <Flex key={key} gap={3} wrap="wrap">
                      <Text fontWeight="semibold" minW="160px">
                        {key}
                      </Text>
                      <Code fontSize="xs" flex="1" wordBreak="break-all" px={2} py={1}>
                        {typeof value === 'string'
                          ? value
                          : JSON.stringify(value)}
                      </Code>
                    </Flex>
                  ))}
                </Stack>
              </SectionCard>
            )}

            {(realmRoles.length > 0 ||
              ownClientRoles.length > 0 ||
              otherClientRoles.length > 0) && (
              <SectionCard title="Roles">
                <Stack spacing={3}>
                  {realmRoles.length > 0 && (
                    <Box>
                      <Text fontSize="xs" color={mutedColor} mb={2}>
                        Realm roles
                      </Text>
                      <Flex wrap="wrap" gap={2}>
                        {realmRoles.map((r) => (
                          <Tag key={`realm-${r}`} colorScheme="blue">
                            {r}
                          </Tag>
                        ))}
                      </Flex>
                    </Box>
                  )}
                  {ownClientRoles.length > 0 && (
                    <Box>
                      <Text fontSize="xs" color={mutedColor} mb={2}>
                        Client roles ({clientId})
                      </Text>
                      <Flex wrap="wrap" gap={2}>
                        {ownClientRoles.map((r) => (
                          <Tag key={`own-${r.role}`} colorScheme="purple">
                            {r.role}
                          </Tag>
                        ))}
                      </Flex>
                    </Box>
                  )}
                  {otherClientRoles.length > 0 && (
                    <Box>
                      <Text fontSize="xs" color={mutedColor} mb={2}>
                        Other client roles
                      </Text>
                      <Flex wrap="wrap" gap={2}>
                        {otherClientRoles.map((r) => (
                          <Tag key={`other-${r.client}-${r.role}`}>
                            {r.client}:{r.role}
                          </Tag>
                        ))}
                      </Flex>
                    </Box>
                  )}
                </Stack>
              </SectionCard>
            )}

            {import.meta.env.DEV && (
              <Accordion allowToggle>
                <AccordionItem border="none">
                  <SectionCard title="Token claims (raw JSON)">
                    <AccordionButton px={0} _hover={{ bg: 'transparent' }}>
                      <Box flex="1" textAlign="left" fontSize="sm" color={mutedColor}>
                        Show all claims from the access token (dev builds only)
                      </Box>
                      <AccordionIcon />
                    </AccordionButton>
                    <AccordionPanel px={0} pt={3}>
                      <Box
                        as="pre"
                        bg={codeBg}
                        p={3}
                        borderRadius="md"
                        fontSize="xs"
                        overflow="auto"
                        maxH="400px"
                      >
                        {JSON.stringify(tokenParsed ?? {}, null, 2)}
                      </Box>
                    </AccordionPanel>
                  </SectionCard>
                </AccordionItem>
              </Accordion>
            )}
          </VStack>
        )}
      </VStack>
    </Box>
  );
};

export default UserProfileView;
