import { ApolloClient, InMemoryCache, createHttpLink, split } from '@apollo/client';
import { getMainDefinition } from '@apollo/client/utilities';
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
import { createClient } from 'graphql-ws';

const httpLink = createHttpLink({
  uri: process.env.NEXT_PUBLIC_GRAPHQL_URL || 'http://localhost:5001/graphql',
});

// WebSocket link for subscriptions (if available)
const wsUrl = process.env.NEXT_PUBLIC_GRAPHQL_WS_URL ||
  (typeof window !== 'undefined'
    ? window.location.origin.replace('http', 'ws') + '/graphql'
    : 'ws://localhost:5001/graphql');

const wsLink = typeof window !== 'undefined' ? new GraphQLWsLink(
  createClient({
    url: wsUrl,
  })
) : null;

// Split link: use WebSocket for subscriptions, HTTP for queries/mutations
const splitLink = typeof window !== 'undefined' && wsLink
  ? split(
    ({ query }) => {
      const definition = getMainDefinition(query);
      return (
        definition.kind === 'OperationDefinition' &&
        definition.operation === 'subscription'
      );
    },
    wsLink,
    httpLink
  )
  : httpLink;

export const apolloClient = new ApolloClient({
  link: splitLink,
  cache: new InMemoryCache(),
});

